import fs from "node:fs";
import path from "node:path";

const sourcePath = process.argv[2];
const outputPath = process.argv[3];

if (!sourcePath || !outputPath) {
  throw new Error(
    "Usage: node build_ace_step15_split_audio_input_workflow.mjs <source.json> <output.json>",
  );
}

const workflow = JSON.parse(fs.readFileSync(sourcePath, "utf8"));

const nodeById = new Map(workflow.nodes.map((node) => [node.id, node]));
const sampler = nodeById.get(3);
const duration = nodeById.get(99);
const vaeLoader = nodeById.get(106);

if (!sampler || !duration || !vaeLoader || !nodeById.has(98)) {
  throw new Error("Unexpected ACE-Step 1.5 split workflow structure.");
}

// Replace the empty latent source with a latent encoded from an uploaded song.
workflow.nodes = workflow.nodes.filter((node) => node.id !== 98);
workflow.links = workflow.links.filter((link) => link[0] !== 250);

duration.outputs[0].links = duration.outputs[0].links.filter((id) => id !== 250);
vaeLoader.outputs[0].links = [...new Set([...vaeLoader.outputs[0].links, 265])];

const latentLink = workflow.links.find((link) => link[0] === 249);
if (!latentLink) {
  throw new Error("Expected latent link 249 was not found.");
}
latentLink[1] = 110;

// Denoise controls how strongly the generated song departs from the input.
sampler.widgets_values[6] = 0.65;

const loadAudioNode = {
  id: 109,
  type: "LoadAudio",
  pos: [-165, -130],
  size: [380, 180],
  flags: {},
  order: 3,
  mode: 0,
  inputs: [
    {
      localized_name: "音訊",
      name: "audio",
      type: "COMBO",
      widget: { name: "audio" },
      link: null,
    },
    {
      localized_name: "音訊介面",
      name: "audioUI",
      type: "AUDIO_UI",
      widget: { name: "audioUI" },
      link: null,
    },
    {
      localized_name: "選擇檔案上傳",
      name: "upload",
      type: "AUDIOUPLOAD",
      widget: { name: "upload" },
      link: null,
    },
  ],
  outputs: [
    {
      localized_name: "音訊",
      name: "AUDIO",
      type: "AUDIO",
      links: [264],
    },
  ],
  title: "Step 2A - 載入原曲 (Load Audio)",
  properties: {
    "Node name for S&R": "LoadAudio",
    cnr_id: "comfy-core",
    ver: "0.11.1",
  },
  widgets_values: ["", null],
  widgets_values_named: { audio: "", upload: null },
};

const encodeAudioNode = {
  id: 110,
  type: "VAEEncodeAudio",
  pos: [-165, 80],
  size: [380, 90],
  flags: {},
  order: 9,
  mode: 0,
  inputs: [
    {
      localized_name: "音訊",
      name: "audio",
      type: "AUDIO",
      link: 264,
    },
    {
      localized_name: "vae",
      name: "vae",
      type: "VAE",
      link: 265,
    },
  ],
  outputs: [
    {
      localized_name: "latent (潛空間)",
      name: "LATENT",
      type: "LATENT",
      links: [249],
    },
  ],
  title: "Step 2B - 原曲特徵提取 (VAE Encode)",
  properties: {
    "Node name for S&R": "VAEEncodeAudio",
    cnr_id: "comfy-core",
    ver: "0.11.1",
  },
  widgets_values: [],
};

const instructionsNode = {
  id: 111,
  type: "MarkdownNote",
  pos: [-180, 405],
  size: [405, 330],
  flags: {},
  order: 10,
  mode: 0,
  inputs: [],
  outputs: [],
  properties: {},
  widgets_values: [
    "# ACE-Step 1.5 原曲改編（分離模型）\n\n" +
      "1. 在「載入原曲」選擇你有權使用的 MP3、WAV 或 FLAC。\n" +
      "2. 將 Song Duration 設成與輸入音樂相同的秒數。\n" +
      "3. 在 Prompt 節點輸入曲風與歌詞。\n" +
      "4. KSampler 的 denoise 控制改編幅度：\n" +
      "   - 0.45～0.55：較保留原曲\n" +
      "   - 0.60～0.70：標準改編（預設 0.65）\n" +
      "   - 0.75～0.85：大幅改編\n" +
      "5. 8 GB VRAM 建議一次只產生 1 首，先用 30～60 秒測試。",
  ],
  widgets_values_named: {
    text:
      "# ACE-Step 1.5 原曲改編（分離模型）\n\n" +
      "1. 在「載入原曲」選擇你有權使用的 MP3、WAV 或 FLAC。\n" +
      "2. 將 Song Duration 設成與輸入音樂相同的秒數。\n" +
      "3. 在 Prompt 節點輸入曲風與歌詞。\n" +
      "4. KSampler 的 denoise 控制改編幅度：\n" +
      "   - 0.45～0.55：較保留原曲\n" +
      "   - 0.60～0.70：標準改編（預設 0.65）\n" +
      "   - 0.75～0.85：大幅改編\n" +
      "5. 8 GB VRAM 建議一次只產生 1 首，先用 30～60 秒測試。",
  },
};

workflow.nodes.push(loadAudioNode, encodeAudioNode, instructionsNode);
workflow.links.push(
  [264, 109, 0, 110, 0, "AUDIO"],
  [265, 106, 0, 110, 1, "VAE"],
);

const orderById = new Map([
  [104, 0],
  [105, 1],
  [106, 2],
  [109, 3],
  [102, 4],
  [99, 5],
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

const durationGroup = workflow.groups.find((group) => group.id === 2);
const promptGroup = workflow.groups.find((group) => group.id === 3);
if (durationGroup) {
  durationGroup.title = "Step 3 - Duration";
  durationGroup.bounding = [-180, 200, 400, 170];
}
duration.pos = [-120, 270];
if (promptGroup) promptGroup.title = "Step 4 - Prompt";
workflow.groups.push({
  id: 4,
  title: "Step 2 - Input Audio",
  bounding: [-180, -180, 405, 370],
  color: "#8A4F7D",
  font_size: 24,
  flags: {},
});

workflow.last_node_id = 111;
workflow.last_link_id = 265;

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(workflow, null, 2)}\n`, "utf8");

