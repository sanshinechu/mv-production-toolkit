import fs from "node:fs";
import path from "node:path";

const sourcePath = process.argv[2];
const outputPath = process.argv[3];

if (!sourcePath || !outputPath) {
  throw new Error(
    "Usage: node build_ace_step15_voice_genre_workflow.mjs <source.json> <output.json>",
  );
}

const workflow = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const textEncode = workflow.nodes.find(
  (node) => node.type === "TextEncodeAceStepAudio1.5",
);
const tempoNode = workflow.nodes.find(
  (node) => node.type === "AudioTempoPreservePitch",
);
if (!textEncode) throw new Error("TextEncodeAceStepAudio1.5 was not found.");
if (!tempoNode) throw new Error("AudioTempoPreservePitch was not found.");

const vocalPresets = [
  "warm expressive male vocal, clear pronunciation, rich midrange",
  "powerful raspy male vocal, energetic belting, strong stage presence",
  "soft airy female vocal, intimate and tender delivery",
  "powerful female vocal, soaring high notes, emotional belting",
  "clear androgynous vocal, smooth controlled delivery",
];

const genrePresets = [
  "live arena pop-rock concert, stadium atmosphere, cheering crowd",
  "emotional piano ballad, cinematic strings, gradual dynamic build",
  "modern R&B soul, warm electric piano, deep bass, laid-back groove",
  "acoustic folk-pop, fingerpicked guitar, organic percussion, intimate room",
  "soulful jazz-pop, Rhodes piano, upright bass, brushed drums, warm saxophone",
  "cinematic orchestral pop, sweeping strings, grand drums, dramatic climax",
  "electronic dance-pop, bright synths, four-on-the-floor beat, festival energy",
  "maximalist K-pop, trap-influenced verses, R&B pre-chorus, explosive synth-pop chorus",
];

const customStyle =
  "polished live-band production, wide stereo soundstage, detailed instrumentation, emotional build, memorable chorus, strong grand finale";

const makeComboNode = ({ id, title, pos, presets, linkId }) => ({
  id,
  type: "CustomCombo",
  pos,
  size: [590, 130],
  flags: {},
  order: id,
  mode: 0,
  inputs: [
    {
      localized_name: "choice",
      name: "choice",
      type: "COMBO",
      widget: { name: "choice" },
      link: null,
    },
  ],
  outputs: [
    { name: "STRING", type: "STRING", links: [linkId] },
    { name: "INDEX", type: "INT", links: null },
  ],
  title,
  properties: { "Node name for S&R": "CustomCombo" },
  widgets_values: [presets[0], 0, ...presets, ""],
});

const makeConcatNode = ({ id, title, pos, inputLinks, outputLink }) => ({
  id,
  type: "StringConcatenate",
  pos,
  size: [340, 170],
  flags: {},
  order: id,
  mode: 0,
  inputs: [
    {
      name: "string_a",
      type: "STRING",
      widget: { name: "string_a" },
      link: inputLinks[0],
    },
    {
      name: "string_b",
      type: "STRING",
      widget: { name: "string_b" },
      link: inputLinks[1],
    },
  ],
  outputs: [{ name: "STRING", type: "STRING", links: [outputLink] }],
  title,
  properties: {
    "Node name for S&R": "StringConcatenate",
    cnr_id: "comfy-core",
    ver: "0.21.0",
  },
  widgets_values: ["", "", ", "],
  widgets_values_named: { string_a: "", string_b: "", delimiter: ", " },
});

const vocalNode = makeComboNode({
  id: 113,
  title: "聲線選擇（Vocal Preset）",
  pos: [900, -1120],
  presets: vocalPresets,
  linkId: 268,
});
const genreNode = makeComboNode({
  id: 114,
  title: "曲風選擇（Genre Preset）",
  pos: [900, -940],
  presets: genrePresets,
  linkId: 269,
});
const customStyleNode = {
  id: 115,
  type: "PrimitiveStringMultiline",
  pos: [270, -1120],
  size: [580, 310],
  flags: {},
  order: 8,
  mode: 0,
  inputs: [],
  outputs: [{ name: "STRING", type: "STRING", links: [270] }],
  title: "自訂曲風細節（Custom Style）",
  properties: { "Node name for S&R": "PrimitiveStringMultiline" },
  widgets_values: [customStyle],
  widgets_values_named: { value: customStyle },
};
const vocalGenreNode = makeConcatNode({
  id: 116,
  title: "合併聲線與曲風",
  pos: [1520, -1120],
  inputLinks: [268, 269],
  outputLink: 271,
});
const finalStyleNode = makeConcatNode({
  id: 117,
  title: "送入 ACE-Step 的完整 Style",
  pos: [1900, -1120],
  inputLinks: [271, 270],
  outputLink: 272,
});

textEncode.inputs.push({
  name: "tags",
  type: "STRING",
  widget: { name: "tags" },
  link: 272,
});
textEncode.inputs.push({
  name: "bpm",
  type: "INT",
  widget: { name: "bpm" },
  link: 273,
});
textEncode.widgets_values[0] = customStyle;
const advancedDefaults = [false, 2.0, 0.85, 0.9, 0, 0.0];
while (textEncode.widgets_values.length < 15) {
  textEncode.widgets_values.push(
    advancedDefaults[textEncode.widgets_values.length - 9],
  );
}
textEncode.widgets_values[9] = false;
textEncode.widgets_values_named ??= {};
textEncode.widgets_values_named.tags = customStyle;
textEncode.widgets_values_named.generate_audio_codes = false;

if (!tempoNode.outputs.some((output) => output.name === "target_bpm")) {
  tempoNode.outputs.push({
    name: "target_bpm",
    type: "INT",
    links: [273],
  });
} else {
  tempoNode.outputs.find((output) => output.name === "target_bpm").links = [273];
}

workflow.nodes.push(
  vocalNode,
  genreNode,
  customStyleNode,
  vocalGenreNode,
  finalStyleNode,
);
workflow.links.push(
  [268, 113, 0, 116, 0, "STRING"],
  [269, 114, 0, 116, 1, "STRING"],
  [270, 115, 0, 117, 1, "STRING"],
  [271, 116, 0, 117, 0, "STRING"],
  [272, 117, 0, textEncode.id, textEncode.inputs.length - 2, "STRING"],
  [273, tempoNode.id, 2, textEncode.id, textEncode.inputs.length - 1, "INT"],
);

workflow.groups.push({
  id: 5,
  title: "Step 3A - 聲線與曲風選擇",
  bounding: [250, -1200, 2010, 430],
  color: "#8A4F7D",
  flags: {},
});

const instructions = workflow.nodes.find((node) => node.id === 111);
if (instructions) {
  const text =
    "# ACE-Step 1.5 原曲改編＋聲線與曲風選擇\n\n" +
    "1. 載入你有權使用的 MP3、WAV 或 FLAC。\n" +
    "2. Source BPM 與 Target BPM 維持手動設定。\n" +
    "3. 在 Vocal Preset 選擇聲線特徵。\n" +
    "4. 在 Genre Preset 選擇曲風。\n" +
    "5. Custom Style 可補充語言、樂器、情緒與演唱會氣氛。\n" +
    "6. 聲線選項是聲音特徵，不會指定或複製真人歌手。\n" +
    "7. KSampler denoise 建議先用 0.60，並先測試 30～60 秒片段。";
  instructions.widgets_values = [text];
  instructions.widgets_values_named = { text };
}

const orderById = new Map([
  [104, 0],
  [105, 1],
  [106, 2],
  [109, 3],
  [112, 4],
  [102, 5],
  [113, 6],
  [114, 7],
  [115, 8],
  [116, 9],
  [117, 10],
  [94, 11],
  [78, 12],
  [47, 13],
  [110, 14],
  [108, 15],
  [111, 16],
  [3, 17],
  [18, 18],
  [107, 19],
]);
for (const node of workflow.nodes) {
  if (orderById.has(node.id)) node.order = orderById.get(node.id);
}

workflow.last_node_id = 117;
workflow.last_link_id = 273;

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(workflow, null, 2)}\n`, "utf8");
