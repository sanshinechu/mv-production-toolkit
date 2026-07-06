// MV Production Workflow Steps - 12 Complete Workflow
const steps = [
  {
    id: "Step_01",
    title: "歌詞創作與曲風風格",
    purpose: "創作適合用 SUNO 生成音樂的歌詞，並編寫英文風格描述。",
    inputs: ["主題", "曲風", "情緒", "目標時長"],
    tools: ["Claude AI", "SUNO AI"],
    outputs: ["完整歌詞（含結構標籤）", "SUNO 風格描述（英文）"],
    time: "30-45 分鐘",
    cost: "$0"
  },
  {
    id: "Step_02",
    title: "主角設計",
    purpose: "設計 MV 主角的外觀和氣質，提供英文影像提示詞。",
    inputs: ["性別", "曲風", "歌詞", "年齡感"],
    tools: ["Claude AI", "FLUX.1 Dev 或 Ideogram"],
    outputs: ["英文影像提示詞", "Split Screen 設計圖", "角色一致性參考詞"],
    time: "15-30 分鐘",
    cost: "$0"
  },
  {
    id: "Step_03",
    title: "場景提示詞設計",
    purpose: "根據歌詞內容設計具體的場景視覺描述（2-4 個場景）。",
    inputs: ["歌詞", "主角設計", "MV 主題"],
    tools: ["Claude AI"],
    outputs: ["2-4 個場景提示詞（各 300-400 字）", "視覺故事線文檔"],
    time: "30-40 分鐘",
    cost: "$0"
  },
  {
    id: "Step_04",
    title: "九宮格分鏡設計",
    purpose: "為每個場景生成 9 宮格分鏡圖，展現不同視角。",
    inputs: ["場景提示詞", "主角設計"],
    tools: ["FLUX.1 Dev 或 FLUX.1 Pro"],
    outputs: ["2-4 張九宮格分鏡圖"],
    time: "30-45 分鐘",
    cost: "$0"
  },
  {
    id: "Step_05",
    title: "截圖放大提質",
    purpose: "從九宮格中選擇 1-3 張關鍵圖片，放大至高解析度。",
    inputs: ["九宮格圖片", "關鍵幀位置"],
    tools: ["Upscayl 或 Topaz Gigapixel AI"],
    outputs: ["3-4 張高解析度圖片（1672×1672+）"],
    time: "10-15 分鐘",
    cost: "$0"
  },
  {
    id: "Step_06",
    title: "影片提示詞設計",
    purpose: "為視頻生成編寫詳細的動態效果描述（運鏡、動作等）。",
    inputs: ["場景提示詞", "九宮格設計", "音樂節奏"],
    tools: ["Claude AI"],
    outputs: ["6 個視頻段提示詞（各 300-500 字）"],
    time: "25-40 分鐘",
    cost: "$0"
  },
  {
    id: "Step_07",
    title: "圖片和影片生成",
    purpose: "使用 AI 工具生成所有視覺素材（圖片和視頻）。",
    inputs: ["主角設計圖", "場景提示詞", "視頻提示詞"],
    tools: ["FLUX.1 Dev/Pro", "Kling V2.1", "Hailuo", "Seedance 2.0"],
    outputs: ["主角設計圖", "場景靜態圖", "6 個視頻段"],
    time: "45-90 分鐘",
    cost: "$1.50-25"
  },
  {
    id: "Step_08",
    title: "空拍視角和細節",
    purpose: "為某些場景添加空拍視角或特殊視角，增加視覺層次感。",
    inputs: ["場景視頻", "運鏡方式"],
    tools: ["Kling / Hailuo / Runway"],
    outputs: ["2-3 個空拍或特殊視角視頻"],
    time: "20-30 分鐘",
    cost: "$0.50"
  },
  {
    id: "Step_09",
    title: "電影感打光優化",
    purpose: "對生成的視頻進行色彩分級和打光優化，提升電影級別質感。",
    inputs: ["生成的視頻"],
    tools: ["DaVinci Resolve", "Adobe Premiere Pro"],
    outputs: ["優化後的視頻段"],
    time: "15-20 分鐘",
    cost: "$0"
  },
  {
    id: "Step_10",
    title: "FFmpeg 組裝與驗證",
    purpose: "將 6 個視頻段和音樂組裝成完整的 MV 文件，檢查音畫同步。",
    inputs: ["視頻段", "音樂文件"],
    tools: ["FFmpeg", "VLC"],
    outputs: ["完整 MV.mp4 文件（3-5 分鐘）"],
    time: "10-15 分鐘",
    cost: "$0"
  },
  {
    id: "Step_11",
    title: "打包與資產整理",
    purpose: "準備 YouTube 上傳所需的所有文件和元數據。",
    inputs: ["完整 MV.mp4", "所有源文件"],
    tools: ["FFmpeg", "文本編輯器"],
    outputs: ["MP4 + PNG 封面 + metadata.md + README.md + CREDITS.md"],
    time: "5-10 分鐘",
    cost: "$0"
  },
  {
    id: "Step_12",
    title: "YouTube 上傳與發布",
    purpose: "上傳到 YouTube 並配置完整的視頻信息。",
    inputs: ["MP4 文件", "metadata.md"],
    tools: ["YouTube Studio 或 youtube_publisher skill"],
    outputs: ["YouTube 視頻連結", "發布統計數據"],
    time: "15-30 分鐘",
    cost: "$0"
  }
];

let activeIndex = 0;

const els = {
  stepNav: document.getElementById("stepNav"),
  activeMeta: document.getElementById("activeMeta"),
  activeTitle: document.getElementById("activeTitle"),
  activeCount: document.getElementById("activeCount"),
  activePurpose: document.getElementById("activePurpose"),
  lyricsInput: document.getElementById("lyricsInput"),
  topicInput: document.getElementById("topicInput"),
  styleInput: document.getElementById("styleInput"),
  moodInput: document.getElementById("moodInput"),
  characterInput: document.getElementById("characterInput"),
  sceneInput: document.getElementById("sceneInput"),
  cameraInput: document.getElementById("cameraInput"),
  generatedPrompt: document.getElementById("generatedPrompt"),
  copyActivePrompt: document.getElementById("copyActivePrompt"),
  resetForm: document.getElementById("resetForm"),
  copyGenerated: document.getElementById("copyGenerated"),
  copyStatus: document.getElementById("copyStatus")
};

function renderNav() {
  els.stepNav.innerHTML = "";
  steps.forEach((step, index) => {
    const button = document.createElement("button");
    button.className = `nav-btn${index === activeIndex ? " active" : ""}`;
    button.type = "button";
    button.innerHTML = `<strong>${step.id}</strong><span>${step.title}</span>`;
    button.addEventListener("click", () => {
      activeIndex = index;
      renderStep();
    });
    els.stepNav.appendChild(button);
  });
}

function renderStep() {
  const step = steps[activeIndex];
  
  if (els.activeMeta) els.activeMeta.textContent = `${step.id} - 進度 ${activeIndex + 1}/${steps.length}`;
  if (els.activeTitle) els.activeTitle.textContent = step.title;
  if (els.activeCount) els.activeCount.textContent = `${activeIndex + 1} / ${steps.length}`;
  if (els.activePurpose) els.activePurpose.textContent = step.purpose;
  
  // Update time and cost
  const stepTime = document.getElementById("stepTime");
  const stepCost = document.getElementById("stepCost");
  if (stepTime) stepTime.textContent = step.time;
  if (stepCost) stepCost.textContent = step.cost;
  
  // Update tools list
  const stepTools = document.getElementById("stepTools");
  if (stepTools) {
    stepTools.innerHTML = step.tools.map(tool => `<li>${tool}</li>`).join('');
  }
  
  // Update inputs list
  const stepInputs = document.getElementById("stepInputs");
  if (stepInputs) {
    stepInputs.innerHTML = step.inputs.map(input => `<li>${input}</li>`).join('');
  }
  
  // Update outputs list
  const stepOutputs = document.getElementById("stepOutputs");
  if (stepOutputs) {
    stepOutputs.innerHTML = step.outputs.map(output => `<li>${output}</li>`).join('');
  }
  
  renderNav();
  console.log("Step changed to:", step.id);
}

function buildPrompt() {
  const lyrics = els.lyricsInput.value.trim() || "";
  const topic = els.topicInput.value.trim() || "";
  const style = els.styleInput.value.trim() || "";
  const mood = els.moodInput.value.trim() || "";
  const character = els.characterInput.value.trim() || "";
  const scene = els.sceneInput.value.trim() || "";
  const camera = els.cameraInput.value.trim() || "";

  const commonPrompt = `歌詞：
${lyrics}

主題：${topic}
曲風：${style}
情緒：${mood}
主角：${character}
場景：${scene}
運鏡：${camera}`;
  if (els.generatedPrompt) els.generatedPrompt.textContent = commonPrompt;
}

function copyPrompt(text) {
  navigator.clipboard.writeText(text).then(() => {
    if (els.copyStatus) {
      els.copyStatus.textContent = "已複製";
      setTimeout(() => { els.copyStatus.textContent = "尚未複製"; }, 2000);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderStep();

  if (els.copyActivePrompt) {
    els.copyActivePrompt.addEventListener("click", () => {
      const step = steps[activeIndex];
      const prompt = `${step.title}\n${step.purpose}`;
      copyPrompt(prompt);
    });
  }

  if (els.resetForm) {
    els.resetForm.addEventListener("click", () => {
      [els.topicInput, els.styleInput, els.moodInput, els.characterInput, els.sceneInput, els.cameraInput].forEach(input => {
        if (input) input.value = "";
      });
      buildPrompt();
    });
  }

  if (els.copyGenerated) {
    els.copyGenerated.addEventListener("click", () => {
      if (els.generatedPrompt) copyPrompt(els.generatedPrompt.textContent);
    });
  }

  [els.topicInput, els.styleInput, els.moodInput, els.characterInput, els.sceneInput, els.cameraInput].forEach(input => {
    if (input) input.addEventListener("input", buildPrompt);
  });
});
