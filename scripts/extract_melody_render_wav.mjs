import fs from 'node:fs';
import path from 'node:path';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('Usage: node extract_melody_render_wav.mjs input.mid output.wav');
  process.exit(2);
}

const data = fs.readFileSync(inputPath);
let pos = 0;
const readU16 = () => { const v = data.readUInt16BE(pos); pos += 2; return v; };
const readU32 = () => { const v = data.readUInt32BE(pos); pos += 4; return v; };
const readStr = n => { const v = data.toString('ascii', pos, pos + n); pos += n; return v; };
const readVar = (buf, state) => {
  let value = 0;
  for (let i = 0; i < 4; i++) {
    const b = buf[state.pos++];
    value = (value << 7) | (b & 0x7f);
    if (!(b & 0x80)) return value;
  }
  throw new Error('Invalid variable-length quantity');
};

if (readStr(4) !== 'MThd') throw new Error('Not a Standard MIDI file');
const headerLength = readU32();
const format = readU16();
const trackCount = readU16();
const division = readU16();
if (division & 0x8000) throw new Error('SMPTE time division is not supported');
pos = 8 + headerLength;

const tempos = [{ tick: 0, usPerQuarter: 500000 }];
const groups = new Map();
let finalTick = 0;

function groupFor(track, channel) {
  const key = `${track}:${channel}`;
  if (!groups.has(key)) groups.set(key, { key, track, channel, notes: [], active: new Map() });
  return groups.get(key);
}

for (let track = 0; track < trackCount; track++) {
  if (readStr(4) !== 'MTrk') throw new Error(`Missing MTrk at track ${track}`);
  const length = readU32();
  const trackData = data.subarray(pos, pos + length);
  pos += length;
  const state = { pos: 0 };
  let tick = 0;
  let runningStatus = null;

  while (state.pos < trackData.length) {
    tick += readVar(trackData, state);
    finalTick = Math.max(finalTick, tick);
    let status = trackData[state.pos++];
    if (status < 0x80) {
      if (runningStatus === null) throw new Error('Running status without prior status');
      state.pos--;
      status = runningStatus;
    } else if (status < 0xf0) {
      runningStatus = status;
    }

    if (status === 0xff) {
      const type = trackData[state.pos++];
      const len = readVar(trackData, state);
      if (type === 0x51 && len === 3) {
        const us = (trackData[state.pos] << 16) | (trackData[state.pos + 1] << 8) | trackData[state.pos + 2];
        tempos.push({ tick, usPerQuarter: us });
      }
      state.pos += len;
      continue;
    }
    if (status === 0xf0 || status === 0xf7) {
      state.pos += readVar(trackData, state);
      continue;
    }

    const kind = status & 0xf0;
    const channel = status & 0x0f;
    const d1 = trackData[state.pos++];
    const d2 = (kind === 0xc0 || kind === 0xd0) ? null : trackData[state.pos++];
    if (channel === 9) continue;
    const group = groupFor(track, channel);
    if (kind === 0x90 && d2 > 0) {
      const stack = group.active.get(d1) ?? [];
      stack.push({ startTick: tick, pitch: d1, velocity: d2 });
      group.active.set(d1, stack);
    } else if (kind === 0x80 || (kind === 0x90 && d2 === 0)) {
      const stack = group.active.get(d1);
      if (stack?.length) {
        const note = stack.shift();
        group.notes.push({ ...note, endTick: Math.max(tick, note.startTick + 1) });
      }
    }
  }
}

for (const group of groups.values()) {
  for (const stack of group.active.values()) {
    for (const note of stack) group.notes.push({ ...note, endTick: Math.max(finalTick, note.startTick + 1) });
  }
  group.notes.sort((a, b) => a.startTick - b.startTick || b.pitch - a.pitch);
}

const candidates = [...groups.values()].filter(g => g.notes.length >= 20).map(g => {
  const avgPitch = g.notes.reduce((s, n) => s + n.pitch, 0) / g.notes.length;
  const onsetCounts = new Map();
  for (const n of g.notes) onsetCounts.set(n.startTick, (onsetCounts.get(n.startTick) ?? 0) + 1);
  const polyOnsets = [...onsetCounts.values()].filter(n => n > 1).length;
  const monophony = 1 - polyOnsets / Math.max(1, onsetCounts.size);
  const score = avgPitch * 2 + monophony * 80 + Math.min(g.notes.length, 600) / 20;
  return { ...g, avgPitch, monophony, score };
}).sort((a, b) => b.score - a.score);

if (!candidates.length) throw new Error('No usable melodic note group found');
const selected = candidates[0];

// Keep one pitch per onset, then prevent overlaps so the result is strictly monophonic.
const byOnset = new Map();
for (const note of selected.notes) {
  const current = byOnset.get(note.startTick);
  if (!current || note.pitch > current.pitch) byOnset.set(note.startTick, { ...note });
}
const melody = [...byOnset.values()].sort((a, b) => a.startTick - b.startTick);
for (let i = 0; i < melody.length - 1; i++) {
  melody[i].endTick = Math.min(melody[i].endTick, melody[i + 1].startTick);
  if (melody[i].endTick <= melody[i].startTick) melody[i].endTick = melody[i].startTick + 1;
}

const tempoMap = [...new Map(tempos.sort((a, b) => a.tick - b.tick).map(t => [t.tick, t])).values()];
function tickToSeconds(targetTick) {
  let seconds = 0;
  let priorTick = 0;
  let tempo = tempoMap[0].usPerQuarter;
  for (let i = 1; i < tempoMap.length && tempoMap[i].tick <= targetTick; i++) {
    seconds += (tempoMap[i].tick - priorTick) * tempo / division / 1e6;
    priorTick = tempoMap[i].tick;
    tempo = tempoMap[i].usPerQuarter;
  }
  return seconds + (targetTick - priorTick) * tempo / division / 1e6;
}

const timed = melody.map(n => ({
  ...n,
  start: tickToSeconds(n.startTick),
  end: tickToSeconds(n.endTick),
}));
const sampleRate = 44100;
const duration = Math.max(...timed.map(n => n.end)) + 1.2;
const samples = new Float32Array(Math.ceil(duration * sampleRate));

for (const note of timed) {
  const start = Math.floor(note.start * sampleRate);
  const end = Math.min(samples.length, Math.ceil((note.end + 0.55) * sampleRate));
  const held = Math.max(0.02, note.end - note.start);
  const freq = 440 * 2 ** ((note.pitch - 69) / 12);
  const gain = 0.16 + 0.34 * (note.velocity / 127);
  for (let i = start; i < end; i++) {
    const t = (i - start) / sampleRate;
    const attack = Math.min(1, t / 0.008);
    const release = t <= held ? 1 : Math.max(0, 1 - (t - held) / 0.55);
    const decay = Math.exp(-1.7 * t);
    const tone = Math.sin(2 * Math.PI * freq * t)
      + 0.38 * Math.sin(2 * Math.PI * freq * 2 * t) * Math.exp(-2.4 * t)
      + 0.16 * Math.sin(2 * Math.PI * freq * 3 * t) * Math.exp(-3.3 * t);
    samples[i] += gain * attack * release * decay * tone;
  }
}

let peak = 0;
for (const s of samples) peak = Math.max(peak, Math.abs(s));
const scale = peak > 0 ? 0.92 / peak : 1;
const pcm = Buffer.alloc(samples.length * 2);
for (let i = 0; i < samples.length; i++) {
  pcm.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(samples[i] * scale * 32767))), i * 2);
}

const wav = Buffer.alloc(44 + pcm.length);
wav.write('RIFF', 0); wav.writeUInt32LE(36 + pcm.length, 4); wav.write('WAVE', 8);
wav.write('fmt ', 12); wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20);
wav.writeUInt16LE(1, 22); wav.writeUInt32LE(sampleRate, 24);
wav.writeUInt32LE(sampleRate * 2, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
wav.write('data', 36); wav.writeUInt32LE(pcm.length, 40); pcm.copy(wav, 44);
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, wav);

console.log(JSON.stringify({
  input: inputPath,
  format,
  division,
  declaredTracks: trackCount,
  candidates: candidates.map(c => ({
    track: c.track,
    channel: c.channel + 1,
    notes: c.notes.length,
    averagePitch: Number(c.avgPitch.toFixed(1)),
    monophony: Number(c.monophony.toFixed(3)),
    score: Number(c.score.toFixed(1)),
  })),
  selected: { track: selected.track, channel: selected.channel + 1 },
  outputNotes: melody.length,
  durationSeconds: Number(duration.toFixed(3)),
  sampleRate,
  channels: 1,
  output: outputPath,
}, null, 2));
