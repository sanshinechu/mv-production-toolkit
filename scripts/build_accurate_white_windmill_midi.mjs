import fs from 'node:fs';
import path from 'node:path';

// Pitch definitions
const pitchByKey = {
  F: { '1': 65, '2': 67, '3': 69, '4': 70, '5': 72, '6': 74, '7': 76, 'i': 77 },
  D: { '1': 62, '2': 64, '3': 66, '4': 67, '5': 69, '6': 71, '7': 73, 'i': 74 },
};

// Bars with explicit rhythmic durations (d = duration in beats, sum per bar must be 4.0)
const scoredBars = [
  // Bars 1 - 4: Intro rests
  { key: 'F', notes: [{ n: '0', d: 4.0 }] },
  { key: 'F', notes: [{ n: '0', d: 4.0 }] },
  { key: 'F', notes: [{ n: '0', d: 4.0 }] },
  { key: 'F', notes: [{ n: '0', d: 4.0 }] },

  // Bar 5: (rest 2.0) 白(1) 色(3) 的(5) 風(7)
  { key: 'F', notes: [
    { n: '0', d: 2.0 },
    { n: '1', d: 0.5 }, { n: '3', d: 0.5 }, { n: '5', d: 0.5 }, { n: '7', d: 0.5 }
  ]},

  // Bar 6: 車(7) ~(i) (rest) 安(1) 靜(3) 的(5) 轉(7)
  { key: 'F', notes: [
    { n: '7', d: 0.5 }, { n: 'i', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '1', d: 0.5 }, { n: '3', d: 0.5 }, { n: '5', d: 0.5 }, { n: '7', d: 0.5 }
  ]},

  // Bar 7: 著(7) ~(i) (rest) 真(5) 實(4) 的(3) 感(4)
  { key: 'F', notes: [
    { n: '7', d: 0.5 }, { n: 'i', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.5 }, { n: '4', d: 0.5 }, { n: '3', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 8: 覺(3) ~(2) (rest) 夢(3) 境(2) 般(1) 遙(5)
  { key: 'F', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '1', d: 0.5 }, { n: '5', d: 0.5 }
  ]},

  // Bar 9: 遠(5) (rest) 甜(1) 甜(3) 的(5) 海(7)
  { key: 'F', notes: [
    { n: '5', d: 1.5 }, { n: '0', d: 0.5 },
    { n: '1', d: 0.5 }, { n: '3', d: 0.5 }, { n: '5', d: 0.5 }, { n: '7', d: 0.5 }
  ]},

  // Bar 10: 水(7) ~(i) (rest) 複(1) 雜(3) 的(5) 眼(7)
  { key: 'F', notes: [
    { n: '7', d: 0.5 }, { n: 'i', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '1', d: 0.5 }, { n: '3', d: 0.5 }, { n: '5', d: 0.5 }, { n: '7', d: 0.5 }
  ]},

  // Bar 11: 淚(7) ~(i) (rest) 看(5) 妳(4) 傻(3) 笑(4)
  { key: 'F', notes: [
    { n: '7', d: 0.5 }, { n: 'i', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.5 }, { n: '4', d: 0.5 }, { n: '3', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 12: 著(3 2) (rest) 握(3) 住(2) 我(1) 的(5)
  { key: 'F', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '0', d: 1.0 },
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '1', d: 0.5 }, { n: '5', d: 0.5 }
  ]},

  // Bar 13: 手(5) (rest) 夢(4) 希(i) 望(i) 沒(7) 有(6) 盡(7)
  { key: 'F', notes: [
    { n: '5', d: 1.0 }, { n: '0', d: 0.5 }, { n: '4', d: 0.5 },
    { n: 'i', d: 0.5 }, { n: 'i', d: 0.5 },
    { n: '7', d: 0.25 }, { n: '6', d: 0.25 }, { n: '7', d: 0.5 }
  ]},

  // Bar 14: 頭(6 5) (rest) 我(5) 們(5) 走(4) 到(3) 這就(4)
  { key: 'F', notes: [
    { n: '6', d: 0.5 }, { n: '5', d: 0.5 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.25 }, { n: '5', d: 0.25 },
    { n: '4', d: 0.5 }, { n: '3', d: 0.5 }, { n: '4', d: 1.0 }
  ]},

  // Bar 15: 好(5 1) (rest) 因(5) 為(5) 我(4) 不(3) 想(4)
  { key: 'F', notes: [
    { n: '5', d: 0.5 }, { n: '1', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.25 }, { n: '5', d: 0.25 },
    { n: '4', d: 0.5 }, { n: '3', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 16: 太(i) 快(i) 走(i) 完(2) 這(3) 幸(1)
  { key: 'F', notes: [
    { n: 'i', d: 0.5 }, { n: 'i', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '2', d: 0.5 },
    { n: '3', d: 1.0 }, { n: '1', d: 1.0 }
  ]},

  // Bar 17: 福(i) (rest) 很(i) 可(i) 惜(7) 沒(6) 有(7)
  { key: 'F', notes: [
    { n: 'i', d: 1.0 }, { n: '0', d: 0.5 }, { n: 'i', d: 0.5 },
    { n: 'i', d: 0.5 }, { n: '7', d: 0.5 }, { n: '6', d: 0.5 }, { n: '7', d: 0.5 }
  ]},

  // Bar 18: 祝(6) 福(5) (rest) 但(5) 愛(5) 妳(i) 並(2) 不(3)
  { key: 'F', notes: [
    { n: '6', d: 0.5 }, { n: '5', d: 1.0 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: 'i', d: 0.5 },
    { n: '2', d: 0.25 }, { n: '3', d: 0.25 }
  ]},

  // Bar 19: 孤(2) 獨(i) (rest) 不(i) 會(i) 再(7) 讓(6) 妳(7)
  { key: 'F', notes: [
    { n: '2', d: 0.5 }, { n: 'i', d: 1.0 }, { n: '0', d: 0.5 },
    { n: 'i', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '7', d: 0.5 },
    { n: '6', d: 0.25 }, { n: '7', d: 0.25 }
  ]},

  // Bar 20: 哭(7)~~~~
  { key: 'F', notes: [
    { n: '7', d: 4.0 }
  ]},

  // Bar 21: (Modulation to D Major) (rest) 我(3) 揹(3) 妳(2)
  { key: 'D', notes: [
    { n: '0', d: 2.5 },
    { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '2', d: 0.5 }
  ]},

  // Bar 22: 走(3) 到(2) 最(2) 後(i) 能(5) 不(5) 能(4)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: 'i', d: 1.0 },
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 23: 不(3) 要(2) 回(2) 頭(i) ~(i) 妳(5) 緊(3)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: 'i', d: 1.0 },
    { n: 'i', d: 0.5 }, { n: '5', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 24: 緊(3) 的(3) 抱(3) 住(2) 我(2) 說(3) 妳(4)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '2', d: 0.5 },
    { n: '2', d: 1.0 }, { n: '3', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 25: 不(5) 需(5) 要(5) 承(5) 諾(7 i 2 2)
  { key: 'D', notes: [
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '5', d: 0.5 },
    { n: '7', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }
  ]},

  // Bar 26: ~(2 1) (rest) 妳(1) 說(2) 我(3)
  { key: 'D', notes: [
    { n: '2', d: 0.5 }, { n: '1', d: 1.0 }, { n: '0', d: 1.0 },
    { n: '1', d: 0.5 }, { n: '2', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 27: 若(3) 一(3) 個(3) 人(2) 會(1) 比(2) 較(3)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '2', d: 0.5 },
    { n: '1', d: 0.5 }, { n: '2', d: 0.5 }, { n: '3', d: 1.0 }
  ]},

  // Bar 28: 自(3) 由(2) ~(2) (rest) 我(5) 不(5) 懂(4)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 1.0 }, { n: '2', d: 0.5 }, { n: '0', d: 0.5 },
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 29: 妳(3) 說(2) 什(2) 麼(i) 反(5) 正(5) 不(4)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: 'i', d: 1.0 },
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 30: 會(3) 鬆(2) 手(2 i) ~(i) 我(5) 揹(3)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: 'i', d: 1.0 },
    { n: 'i', d: 0.5 }, { n: '5', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 31: 妳(3) 走(3) 到(3) 最(2) 後(i) 能(5) 不(3)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '2', d: 0.5 },
    { n: 'i', d: 1.0 }, { n: '5', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 32: 能(3) 別(3) 想(3) 太(2) 多(2) 會(3) 不(4)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '3', d: 0.5 }, { n: '2', d: 0.5 },
    { n: '2', d: 1.0 }, { n: '3', d: 0.5 }, { n: '4', d: 0.5 }
  ]},

  // Bar 33: 會(5) 手(5) 牽(5) 著(5) 手(7 i 2 2)
  { key: 'D', notes: [
    { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '5', d: 0.5 }, { n: '5', d: 0.5 },
    { n: '7', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }
  ]},

  // Bar 34: ~(2 1) (rest) 晚(1) 一(2) 點(3)
  { key: 'D', notes: [
    { n: '2', d: 0.5 }, { n: '1', d: 1.0 }, { n: '0', d: 1.0 },
    { n: '1', d: 0.5 }, { n: '2', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 35: 才(3) 到(2) 盡(2) 頭(2) ~(i) 妳(2) 說(3)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 },
    { n: 'i', d: 1.0 }, { n: '2', d: 0.5 }, { n: '3', d: 0.5 }
  ]},

  // Bar 36: 不(3) 該(2) 再(i) 相(7) 見(i)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '7', d: 0.5 },
    { n: 'i', d: 2.0 }
  ]},

  // Bar 37: 見(i held)
  { key: 'D', notes: [{ n: 'i', d: 2.0 }, { n: '0', d: 2.0 }] },

  // Bars 38 - 41: Interlude rests
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },

  // Bar 42:
  { key: 'D', notes: [{ n: 'i', d: 2.0 }, { n: '0', d: 2.0 }] },

  // Bar 43: (rest) 謝(i) 謝(i) 妳(2)
  { key: 'D', notes: [
    { n: '0', d: 2.5 },
    { n: 'i', d: 0.5 }, { n: 'i', d: 0.5 }, { n: '2', d: 0.5 }
  ]},

  // Bar 44: 讓(3) 我(2) 聽(2) 見(2 i) 因(i) 為(2)
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 }, { n: '2', d: 0.5 },
    { n: 'i', d: 1.0 }, { n: 'i', d: 0.5 }, { n: '2', d: 0.5 }
  ]},

  // Bar 45: 我(3) 在(2) 等(1) 待(7) 永(i) 遠
  { key: 'D', notes: [
    { n: '3', d: 0.5 }, { n: '2', d: 0.5 }, { n: '1', d: 0.5 }, { n: '7', d: 0.5 },
    { n: 'i', d: 2.0 }
  ]},

  // Bar 46: 遠(i held)
  { key: 'D', notes: [{ n: 'i', d: 2.0 }, { n: '0', d: 2.0 }] },

  // Bars 47 - 48: Outro rests
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },
  { key: 'D', notes: [{ n: '0', d: 4.0 }] },
];

// Validate all bars sum to 4.0
for (let b = 0; b < scoredBars.length; b++) {
  const sum = scoredBars[b].notes.reduce((acc, n) => acc + n.d, 0);
  if (Math.abs(sum - 4.0) > 0.001) {
    console.error(`Error in Bar ${b + 1}: sum of durations is ${sum} instead of 4.0`);
    process.exit(1);
  }
}
console.log(`Validated ${scoredBars.length} bars, all strictly 4.0 beats!`);

const outPath = process.argv[2] || 'outputs/白色風車_單音/白色風車_原曲速度_單音旋律.mid';
const bpm = Number(process.argv[3] ?? 71);
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
for (const bar of scoredBars) {
  const pitchMap = pitchByKey[bar.key];
  for (const item of bar.notes) {
    const ticks = Math.round(item.d * division);
    if (item.n === '0' || !pitchMap[item.n]) {
      pendingRestTicks += ticks;
    } else {
      const p = pitchMap[item.n];
      // Articulation: note-on for 90% of duration, 10% rest between adjacent notes so repeated notes articulate clearly
      const noteTicks = Math.max(1, Math.round(ticks * 0.90));
      const releaseTicks = ticks - noteTicks;
      track.push(...vlq(pendingRestTicks), 0x90, p, 96, ...vlq(noteTicks), 0x80, p, 0);
      pendingRestTicks = releaseTicks;
    }
  }
}
track.push(...vlq(pendingRestTicks), 0xff, 0x2f, 0x00);

const header = Buffer.alloc(6);
header.writeUInt16BE(0, 0); header.writeUInt16BE(1, 2); header.writeUInt16BE(division, 4);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, Buffer.concat([chunk('MThd', header), chunk('MTrk', track)]));
console.log(`Successfully generated ${outPath} (${scoredBars.length} bars at ${bpm} BPM).`);
