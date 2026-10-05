import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const sourcePath = process.argv[2];
const outputPath = process.argv[3];

if (!sourcePath || !outputPath) {
  throw new Error(
    "Usage: node build_yue2_cover_adjustable_bpm_workflow.mjs <source.json> <output.json>",
  );
}

const workflow = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const subgraph = workflow.definitions?.subgraphs?.find(
  (item) => item.name === "Music Cover (YuE2)",
);
const instance = workflow.nodes.find((node) => node.type === subgraph?.id);

if (!subgraph || !instance) {
  throw new Error("YuE2 Music Cover subgraph was not found.");
}

const generator = subgraph.nodes.find((node) => node.type === "YuE2GenerateMusic");
if (!generator) throw new Error("YuE2GenerateMusic was not found.");

const inputIndex = (node, name) => {
  const index = node.inputs.findIndex((input) => input.name === name);
  if (index < 0) throw new Error(`Input ${name} was not found on ${node.type}.`);
  return index;
};

const maxId = (items, field = "id") =>
  items.reduce((maximum, item) => Math.max(maximum, Number(item[field]) || 0), 0);

const makeConcatNode = ({ id, title, pos, links, values, inputs }) => ({
  id,
  type: "StringConcatenate",
  pos,
  size: [330, 170],
  flags: {},
  order: id,
  mode: 0,
  inputs,
  outputs: [{ name: "STRING", type: "STRING", links }],
  title,
  properties: {
    "Node name for S&R": "StringConcatenate",
    cnr_id: "comfy-core",
    ver: "0.21.0",
  },
  widgets_values: values,
  widgets_values_named: {
    string_a: values[0],
    string_b: values[1],
    delimiter: values[2],
  },
});

const vocalPresets = [
  "Mandarin, warm expressive male vocal, clear pronunciation",
  "Mandarin, powerful raspy male vocal, energetic belting",
  "Mandarin, soft airy female vocal, intimate and tender delivery",
  "Mandarin, powerful female vocal, soaring high notes and emotional belting",
  "Mandarin, clear androgynous vocal, smooth controlled delivery",
];

const genrePresets = [
  "live arena pop-rock concert, stadium atmosphere, cheering crowd",
  "emotional piano ballad, cinematic strings, gradual dynamic build",
  "modern R&B soul, warm electric piano, deep bass, laid-back groove",
  "acoustic folk-pop, fingerpicked guitar, organic percussion, intimate room",
  "soulful jazz-pop, Rhodes piano, upright bass, brushed drums, warm saxophone",
  "cinematic orchestral pop, sweeping strings, grand drums, dramatic climax",
  "electronic dance-pop, bright synths, four-on-the-floor beat, festival energy",
];

const ids = {
  bpmConcat: 147,
  bpmRegex: 148,
  bpmPreview: 149,
  vocalGenre: 150,
  customStyle: 151,
  bpmPrompt: 152,
  finalStyle: 153,
  vocalCombo: 154,
  genreCombo: 155,
};

const linkIds = {
  bpmInput: 198,
  bpmLine: 199,
  bpmPreview: 200,
  bpmGenerator: 201,
  vocalInput: 202,
  genreInput: 203,
  vocalGenre: 204,
  customStyle: 205,
  bpmPromptInput: 206,
  bpmPrompt: 207,
  finalStyle: 208,
  rootVocal: 209,
  rootGenre: 210,
};

let bpmInput = subgraph.inputs.find((input) => input.name === "target_bpm");
if (!bpmInput) {
  const abcIndex = inputIndex(generator, "abc");
  const oldAbcLink = subgraph.links.find(
    (link) => link.target_id === generator.id && link.target_slot === abcIndex,
  );
  if (!oldAbcLink) throw new Error("The original ABC-to-YuE2 link was not found.");

  const bpmSlot = subgraph.inputs.length;
  bpmInput = {
    id: crypto.randomUUID(),
    name: "target_bpm",
    type: "STRING",
    linkIds: [linkIds.bpmInput],
    label: "Target BPM (number only)",
    pos: [-695.033203125, -386],
  };
  subgraph.inputs.push(bpmInput);

  const bpmConcatNode = makeConcatNode({
    id: ids.bpmConcat,
    title: "建立 ABC 節拍行",
    pos: [250, -380],
    links: [linkIds.bpmLine],
    values: ["Q:1/4=", "", ""],
    inputs: [
      {
        name: "string_b",
        type: "STRING",
        widget: { name: "string_b" },
        link: linkIds.bpmInput,
      },
    ],
  });

  const regexNode = {
    id: ids.bpmRegex,
    type: "RegexReplace",
    pos: [620, -400],
    size: [400, 350],
    flags: {},
    order: ids.bpmRegex,
    mode: 0,
    showAdvanced: true,
    inputs: [
      { name: "string", type: "STRING", widget: { name: "string" }, link: oldAbcLink.id },
      { name: "replace", type: "STRING", widget: { name: "replace" }, link: linkIds.bpmLine },
    ],
    outputs: [{ name: "STRING", type: "STRING", links: [linkIds.bpmPreview] }],
    title: "將 ABC 節拍改成 Target BPM",
    properties: {
      "Node name for S&R": "RegexReplace",
      cnr_id: "comfy-core",
      ver: "0.21.0",
    },
    widgets_values: ["", "^Q\\s*:.*$", "", false, true, false, 1],
    widgets_values_named: {
      string: "",
      regex_pattern: "^Q\\s*:.*$",
      replace: "",
      case_insensitive: false,
      multiline: true,
      dotall: false,
      count: 1,
    },
  };

  const previewNode = {
    id: ids.bpmPreview,
    type: "PreviewAny",
    pos: [1080, -370],
    size: [470, 300],
    flags: {},
    order: ids.bpmPreview,
    mode: 0,
    inputs: [{ name: "source", type: "*", link: linkIds.bpmPreview }],
    outputs: [{ name: "STRING", type: "STRING", links: [linkIds.bpmGenerator] }],
    title: "修改後 ABC（確認 Q: 節拍）",
    properties: { "Node name for S&R": "PreviewAny" },
    widgets_values: [],
    widgets_values_named: {},
  };

  oldAbcLink.target_id = ids.bpmRegex;
  oldAbcLink.target_slot = 0;
  generator.inputs[abcIndex].link = linkIds.bpmGenerator;
  subgraph.nodes.push(bpmConcatNode, regexNode, previewNode);
  subgraph.links.push(
    { id: linkIds.bpmInput, origin_id: -10, origin_slot: bpmSlot, target_id: ids.bpmConcat, target_slot: 0, type: "STRING" },
    { id: linkIds.bpmLine, origin_id: ids.bpmConcat, origin_slot: 0, target_id: ids.bpmRegex, target_slot: 1, type: "STRING" },
    { id: linkIds.bpmPreview, origin_id: ids.bpmRegex, origin_slot: 0, target_id: ids.bpmPreview, target_slot: 0, type: "STRING" },
    { id: linkIds.bpmGenerator, origin_id: ids.bpmPreview, origin_slot: 0, target_id: generator.id, target_slot: abcIndex, type: "STRING" },
  );

  instance.size[1] = Math.max(instance.size[1], 490);
  instance.inputs.push({
    label: "Target BPM (number only)",
    name: "target_bpm",
    type: "STRING",
    widget: { name: "target_bpm" },
    link: null,
  });
  instance.widgets_values.push("150");
  instance.widgets_values_named ??= {};
  instance.widgets_values_named.target_bpm = "150";
}

if (!subgraph.inputs.some((input) => input.name === "vocal_preset")) {
  const styleIndex = inputIndex(generator, "style");
  const oldStyleLink = subgraph.links.find(
    (link) => link.target_id === generator.id && link.target_slot === styleIndex,
  );
  if (!oldStyleLink) throw new Error("The original Style-to-YuE2 link was not found.");

  const bpmSlot = subgraph.inputs.findIndex((input) => input.name === "target_bpm");
  const vocalSlot = subgraph.inputs.length;
  const genreSlot = vocalSlot + 1;
  subgraph.inputs.push(
    {
      id: crypto.randomUUID(),
      name: "vocal_preset",
      type: "STRING",
      linkIds: [linkIds.vocalInput],
      label: "Vocal preset",
      pos: [-695.033203125, -366],
    },
    {
      id: crypto.randomUUID(),
      name: "genre_preset",
      type: "STRING",
      linkIds: [linkIds.genreInput],
      label: "Genre preset",
      pos: [-695.033203125, -346],
    },
  );
  bpmInput.linkIds.push(linkIds.bpmPromptInput);

  const vocalGenreNode = makeConcatNode({
    id: ids.vocalGenre,
    title: "合併聲線與曲風",
    pos: [250, -930],
    links: [linkIds.vocalGenre],
    values: ["", "", ", "],
    inputs: [
      { name: "string_a", type: "STRING", widget: { name: "string_a" }, link: linkIds.vocalInput },
      { name: "string_b", type: "STRING", widget: { name: "string_b" }, link: linkIds.genreInput },
    ],
  });
  const customStyleNode = makeConcatNode({
    id: ids.customStyle,
    title: "加入自訂 Style",
    pos: [620, -930],
    links: [linkIds.customStyle],
    values: ["", "", ", "],
    inputs: [
      { name: "string_a", type: "STRING", widget: { name: "string_a" }, link: linkIds.vocalGenre },
      { name: "string_b", type: "STRING", widget: { name: "string_b" }, link: oldStyleLink.id },
    ],
  });
  const bpmPromptNode = makeConcatNode({
    id: ids.bpmPrompt,
    title: "建立 BPM 曲風描述",
    pos: [620, -700],
    links: [linkIds.bpmPrompt],
    values: ["target BPM ", "", ""],
    inputs: [
      { name: "string_b", type: "STRING", widget: { name: "string_b" }, link: linkIds.bpmPromptInput },
    ],
  });
  const finalStyleNode = makeConcatNode({
    id: ids.finalStyle,
    title: "送入 YuE2 的完整曲風",
    pos: [1080, -930],
    links: [linkIds.finalStyle],
    values: ["", "", ", "],
    inputs: [
      { name: "string_a", type: "STRING", widget: { name: "string_a" }, link: linkIds.customStyle },
      { name: "string_b", type: "STRING", widget: { name: "string_b" }, link: linkIds.bpmPrompt },
    ],
  });

  oldStyleLink.target_id = ids.customStyle;
  oldStyleLink.target_slot = 1;
  generator.inputs[styleIndex].link = linkIds.finalStyle;
  subgraph.nodes.push(vocalGenreNode, customStyleNode, bpmPromptNode, finalStyleNode);
  subgraph.links.push(
    { id: linkIds.vocalInput, origin_id: -10, origin_slot: vocalSlot, target_id: ids.vocalGenre, target_slot: 0, type: "STRING" },
    { id: linkIds.genreInput, origin_id: -10, origin_slot: genreSlot, target_id: ids.vocalGenre, target_slot: 1, type: "STRING" },
    { id: linkIds.vocalGenre, origin_id: ids.vocalGenre, origin_slot: 0, target_id: ids.customStyle, target_slot: 0, type: "STRING" },
    { id: linkIds.customStyle, origin_id: ids.customStyle, origin_slot: 0, target_id: ids.finalStyle, target_slot: 0, type: "STRING" },
    { id: linkIds.bpmPromptInput, origin_id: -10, origin_slot: bpmSlot, target_id: ids.bpmPrompt, target_slot: 0, type: "STRING" },
    { id: linkIds.bpmPrompt, origin_id: ids.bpmPrompt, origin_slot: 0, target_id: ids.finalStyle, target_slot: 1, type: "STRING" },
    { id: linkIds.finalStyle, origin_id: ids.finalStyle, origin_slot: 0, target_id: generator.id, target_slot: styleIndex, type: "STRING" },
  );

  const vocalTargetSlot = instance.inputs.length;
  const genreTargetSlot = vocalTargetSlot + 1;
  instance.inputs.push(
    { label: "Vocal preset", name: "vocal_preset", type: "STRING", link: linkIds.rootVocal },
    { label: "Genre preset", name: "genre_preset", type: "STRING", link: linkIds.rootGenre },
  );

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

  workflow.nodes.push(
    makeComboNode({ id: ids.vocalCombo, title: "聲線選擇（Vocal Preset）", pos: [800, -520], presets: vocalPresets, linkId: linkIds.rootVocal }),
    makeComboNode({ id: ids.genreCombo, title: "曲風選擇（Genre Preset）", pos: [800, -690], presets: genrePresets, linkId: linkIds.rootGenre }),
  );
  workflow.links.push(
    [linkIds.rootVocal, ids.vocalCombo, 0, instance.id, vocalTargetSlot, "STRING"],
    [linkIds.rootGenre, ids.genreCombo, 0, instance.id, genreTargetSlot, "STRING"],
  );
}

if (!workflow.nodes.some((node) => node.type === "LoadAudio")) {
  const audioTargetSlot = instance.inputs.findIndex((input) => input.name === "audio");
  if (audioTargetSlot < 0) throw new Error("The Music Cover audio input was not found.");
  const audioOutputSlot = instance.outputs.findIndex((output) => output.name === "AUDIO");
  if (audioOutputSlot < 0) throw new Error("The Music Cover audio output was not found.");

  const loadAudioNode = {
    id: 156,
    type: "LoadAudio",
    pos: [800, -260],
    size: [590, 180],
    flags: {},
    order: 0,
    mode: 0,
    inputs: [],
    outputs: [{ name: "AUDIO", type: "AUDIO", links: [211] }],
    title: "載入要翻唱的參考音樂",
    properties: { "Node name for S&R": "LoadAudio" },
    widgets_values: ["yue2_reference_song.flac", null, null],
    widgets_values_named: { audio: "yue2_reference_song.flac", upload: null },
  };

  const saveAudioNode = {
    id: 157,
    type: "SaveAudioAdvanced",
    pos: [2020, -260],
    size: [700, 140],
    flags: {},
    order: 20,
    mode: 0,
    inputs: [{ name: "audio", type: "AUDIO", link: 212 }],
    outputs: [{ name: "audio", type: "AUDIO", links: [] }],
    title: "儲存 YuE2 翻唱音樂",
    properties: { "Node name for S&R": "SaveAudioAdvanced" },
    widgets_values: ["audio/YuE2_cover", "flac"],
    widgets_values_named: { filename_prefix: "audio/YuE2_cover", format: "flac" },
  };

  const noteText =
    "# YuE2 音樂翻唱：聲線、曲風與 BPM 可調\n\n" +
    "1. 在「載入要翻唱的參考音樂」選擇音訊。\n" +
    "2. 在聲線與曲風下拉選單挑選預設。\n" +
    "3. 在 Music Cover 節點手動填入 Target BPM。\n" +
    "4. 在 Music Cover 節點填入自訂 Style 與歌詞。\n" +
    "5. 執行後由右側節點儲存 FLAC。\n\n" +
    "聲線選單描述的是演唱特徵，不是指定或複製真人歌手。";
  const noteNode = {
    id: 158,
    type: "MarkdownNote",
    pos: [180, -260],
    size: [550, 620],
    flags: {},
    order: 1,
    mode: 0,
    inputs: [],
    outputs: [],
    properties: {},
    widgets_values: [noteText],
    widgets_values_named: { text: noteText },
    color: "#222",
    bgcolor: "#000",
  };

  instance.pos = [1440, -260];
  instance.inputs[audioTargetSlot].link = 211;
  instance.outputs[audioOutputSlot].links = [212];
  workflow.nodes.push(loadAudioNode, saveAudioNode, noteNode);
  workflow.links.push(
    [211, 156, 0, instance.id, audioTargetSlot, "AUDIO"],
    [212, instance.id, audioOutputSlot, 157, 0, "AUDIO"],
  );
}

const originalStyle =
  "Mandarin lyrics, grand piano and acoustic guitar intro, dynamic live-band arrangement, authentic concert hall reverb, wide stereo soundstage, emotional climax, polished organic production";
instance.widgets_values[0] = originalStyle;
instance.widgets_values_named ??= {};
instance.widgets_values_named.value = originalStyle;
instance.size[1] = Math.max(instance.size[1], 540);

const note = workflow.nodes.find((node) => node.type === "MarkdownNote");
if (note) {
  let text = String(note.widgets_values?.[0] ?? "");
  if (!text.includes("## Adjustable BPM")) {
    text +=
      "\n\n## Adjustable BPM\n\n" +
      "Set **Target BPM** on the Music Cover node. The workflow replaces the " +
      "`Q:` tempo line in the SheetSage2 ABC score before YuE2 generation. " +
      "Open the subgraph and check **Modified ABC** to confirm the requested value.";
  }
  if (!text.includes("## Vocal and Genre Presets")) {
    text +=
      "\n\n## Vocal and Genre Presets\n\n" +
      "Choose a vocal character in **Vocal Preset** and an arrangement in " +
      "**Genre Preset**. Keep **Style** for language, instruments, mood, venue " +
      "and production details. The workflow combines both presets, custom Style " +
      "and Target BPM before sending them to YuE2. These presets describe vocal " +
      "characteristics; they do not clone or select a named real singer.";
  }
  note.widgets_values = [text];
  note.widgets_values_named ??= {};
  note.widgets_values_named.text = text;
}

subgraph.state.lastNodeId = maxId(subgraph.nodes);
subgraph.state.lastLinkId = maxId(subgraph.links);
workflow.last_node_id = Math.max(maxId(workflow.nodes), subgraph.state.lastNodeId);
workflow.last_link_id = Math.max(
  workflow.links.reduce((maximum, link) => Math.max(maximum, Number(link[0]) || 0), 0),
  subgraph.state.lastLinkId,
);

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(workflow, null, 2)}\n`, "utf8");
