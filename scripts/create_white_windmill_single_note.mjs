import fs from 'node:fs';
import path from 'node:path';

const outPath = process.argv[2];
if (!outPath) throw new Error('Usage: node create_white_windmill_single_note.mjs <output.mid>');
const bpm = Number(process.argv[3] ?? 65);
if (!Number.isFinite(bpm) || bpm <= 0) throw new Error('BPM must be a positive number.');

// Monophonic study transcription based on the publicly viewable numbered-score preview.
// 0 and - are rests; each bar is fitted into 4 beats at 65 BPM.
const bars = [
  '0000','0000','0000','0000',
  '0000','01357','7i01357','7i05434',
  '3203215','501357','7i01357','7i05434',
  '323215','54ii767','65055434','51055434',
  'iii231','i0ii767','6555i23','2i0ii767',
  '7---','0332','322i554','322ii53',
  '3332234','55557122','210123','3332123',
  '3220554','322i554','322ii53','3332i53',
  '3332234','55557122','210123','3222i23',
  '32i7i','i000','0000','0000',
  '0000','i000','00 0i i2','3222i i2',
  '3217i','i000','0000','0000'
];

// The source score begins in F major and changes to D major at bar 21.
const pitchByKey = {
  F: { '1': 65, '2': 67, '3': 69, '4': 70, '5': 72, '6': 74, '7': 76, i: 77 },
  D: { '1': 62, '2': 64, '3': 66, '4': 67, '5': 69, '6': 71, '7': 73, i: 74 },
};
const division = 480;
const tempo = Math.round(60_000_000 / bpm);

function vlq(value) {
  const bytes = [value & 0x7f];
  while ((value >>= 7)) bytes.unshift((value & 0x7f) | 0x80);
  return bytes;
}
function chunk(id, payload) {
  const head = Buffer.alloc(8);
  head.write(id, 0, 4, 'ascii');
  head.writeUInt32BE(payload.length, 4);
  return Buffer.concat([head, Buffer.from(payload)]);
}

const track = [
  0x00, 0xff, 0x51, 0x03, (tempo >> 16) & 255, (tempo >> 8) & 255, tempo & 255,
  0x00, 0xff, 0x58, 0x04, 4, 2, 24, 8,
  0x00, 0xc0, 0x00,
];
let pendingRestTicks = 0;
for (const [barIndex, bar] of bars.entries()) {
  const pitch = barIndex < 20 ? pitchByKey.F : pitchByKey.D;
  const notes = [...bar].filter(ch => pitch[ch] || ch === '0' || ch === '-');
  const ticks = Math.round((division * 4) / notes.length);
  for (const token of notes) {
    if (pitch[token]) {
      track.push(...vlq(pendingRestTicks), 0x90, pitch[token], 92, ...vlq(ticks), 0x80, pitch[token], 0);
      pendingRestTicks = 0;
    } else {
      pendingRestTicks += ticks;
    }
  }
}
track.push(...vlq(pendingRestTicks), 0xff, 0x2f, 0x00);

const header = Buffer.alloc(6);
header.writeUInt16BE(0, 0); header.writeUInt16BE(1, 2); header.writeUInt16BE(division, 4);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, Buffer.concat([chunk('MThd', header), chunk('MTrk', track)]));
console.log(`Wrote ${outPath} (${bars.length} bars at ${bpm} BPM).`);
