import fs from "node:fs";
import path from "node:path";

const sourcePath = process.argv[2];
const outputPath = process.argv[3];

if (!sourcePath || !outputPath) {
  throw new Error(
    "Usage: node build_ace_step15_tempo_workflow.mjs <source.json> <output.json>",
  );
}

const workflow = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const nodes = new Map(workflow.nodes.map((node) => [node.id, node]));
const loadAudio = nodes.get(109);
const vaeEncode = nodes.get(110);
const textEncode = nodes.get(94);
const sampler = nodes.get(3);

if (!loadAudio || !vaeEncode || !textEncode || !sampler) {
  throw new Error("Expected the ACE-Step audio-input workflow as the source.");
}

// Remove the manual duration node and its old duration link.
workflow.nodes = workflow.nodes.filter((node) => node.id !== 99);
workflow.links = workflow.links.filter((link) => link[0] !== 251);
workflow.groups = workflow.groups.filter((group) => group.id !== 2);

// Existing link 264 now feeds the tempo node instead of VAEEncodeAudio.
const inputAudioLink = workflow.links.find((link) => link[0] === 264);
if (!inputAudioLink) throw new Error("Input audio link 264 was not found.");
inputAudioLink[3] = 112;
inputAudioLink[4] = 0;

vaeEncode.inputs[0].link = 266;
textEncode.inputs.find((input) => input.name === "duration").link = 267;
// The ACE-Step node itself recommends disabling generated audio codes when an
// audio reference is supplied, avoiding competing structural guidance.
if (Array.isArray(textEncode.widgets_values) && textEncode.widgets_values.length > 9) {
  textEncode.widgets_values[9] = false;
}
if (textEncode.widgets_values_named) {
  textEncode.widgets_values_named.generate_audio_codes = false;
}
sampler.widgets_values[6] = 0.60;

const tempoNode = {
  id: 112,
  type: "AudioTempoPreservePitch",
  pos: [-165, 80],
  size: [380, 120],
  flags: {},
  order: 4,
  mode: 0,
  inputs: [
    {
      name: "audio",
      type: "AUDIO",
      link: 264,
    },
  ],
  outputs: [
    {
      name: "audio",
      type: "AUDIO",
      links: [266],
    },
    {
      name: "duration_seconds",
      type: "FLOAT",
      links: [267],
    },
  ],
  title: "Step 2B - 修改 BPM（保持音高）",
  properties: {
    "Node name for S&R": "AudioTempoPreservePitch",
  },
  widgets_values: [124.0, 150.0],
};

vaeEncode.pos = [-165, 240];
vaeEncode.title = "Step 2C - 原曲特徵提取 (VAE Encode)";
workflow.nodes.push(tempoNode);
workflow.links.push(
  [266, 112, 0, 110, 0, "AUDIO"],
  [267, 112, 1, 94, 2, "FLOAT"],
);

const inputGroup = workflow.groups.find((group) => group.id === 4);
if (inputGroup) {
  inputGroup.bounding = [-180, -180, 405, 540];
}
const promptGroup = workflow.groups.find((group) => group.id === 3);
if (promptGroup) promptGroup.title = "Step 3 - Prompt";

const instructions = workflow.nodes.find((node) => node.id === 111);
if (instructions) {
  instructions.pos = [-180, 390];
  const text =
    "# ACE-Step 1.5 原曲改編＋真正修改 BPM\n\n" +
    "1. 載入你有權使用的 MP3、WAV 或 FLAC。\n" +
    "2. Source BPM 填入原曲實測速度。\n" +
    "3. Target BPM 填入想要的新速度。\n" +
    "4. 節點會用 FFmpeg 改變速度但維持音高。\n" +
    "5. 新時長會自動送入 ACE-Step Prompt，不必手動計算。\n" +
    "6. KSampler denoise 建議先用 0.60。\n" +
    "7. 8 GB VRAM 建議先用 30～60 秒片段測試。";
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
  [94, 6],
  [78, 7],
  [47, 8],
  [110, 9],
  [108, 10],
  [111, 11],
  [3, 12],
  [18, 13],
  [107, 14],
]);
for (const node of workflow.nodes) {
  if (orderById.has(node.id)) node.order = orderById.get(node.id);
}

workflow.last_node_id = 112;
workflow.last_link_id = 267;

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(workflow, null, 2)}\n`, "utf8");
