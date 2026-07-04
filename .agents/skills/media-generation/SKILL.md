---
name: AI 多媒體生成器
description: 生成高品質圖片和影片。生圖支援 FLUX.1/Ideogram，生影片支援 Kling/Hailuo/Dreamina Seedance 2.0（電影感）
triggers: 生圖、生影片、生成圖片、生成影片、AI 繪圖、AI 影片、Dreamina、FLUX、Kling、Hailuo
version: 2.0.0
author: 阿亮老師・3A科技研究社
---

## 🎨 功能說明

這是一個全能的 AI 多媒體生成工具，支援：
- ✅ **生圖**：FLUX.1 Dev/Pro、Ideogram V3（$0.03-0.05/張）
- ✅ **生影片（快速版）**：Kling V2.1、Hailuo（$0.07-0.28/秒）
- ✅ **生影片（電影感）**：Dreamina Seedance 2.0（$0.15-0.30/秒）
- ✅ **讀圖/OCR**：使用 Codex 視覺或 Gemini Vision

---

## 🚀 快速開始

### 環境需求
- ✅ `FAL_KEY` 環境變數已設定
- ✅ Python 環境（生影片需要）
- ✅ curl（已內建）

### 生圖模型對比

| 模型 | 特色 | 價格 | 場景 |
|------|------|------|------|
| **FLUX.1 Dev** | 高品質、平衡 | $0.025/張 | 推薦首選 |
| **FLUX.1 Pro** | 最高品質 | $0.05/張 | 要求極高 |
| **Ideogram V3** | 文字渲染強 | $0.03-0.09 | 有文字需求 |
| **FLUX Schnell** | 最快最便宜 | $0.003/張 | 快速草稿 |

### 生影片模型對比

| 模型 | 特色 | 價格 | 時長 | 場景 |
|------|------|------|------|------|
| **Kling V2.1** | 臉部表情最強 | $0.07/秒 | 最多 5 秒 | 人物重點 |
| **Hailuo** | 電影感、低成本 | $0.28/6秒 | 6-12 秒 | 場景轉換 |
| **Wan 2.1** | 便宜快速 | $0.10/秒 | 最多 5 秒 | 預算優先 |
| **Seedance 2.0** | 頂級電影感 | $0.15-0.30/秒 | 最多 10 秒 | MV 高潮片段 |

---

## 💡 在 MV 製作中的應用

### 階段 1：歌詞→音樂（使用 SUNO）
1. 使用 **MV_01** 創作歌詞和風格描述
2. 複製 SUNO 風格描述到 SUNO 官網
3. SUNO 生成音樂（30-60 秒）

### 階段 2：靜態圖→生圖
1. 使用 **MV_02/03** 的提示詞
2. 選擇 **FLUX.1 Dev** 或 **Ideogram V3**
3. 生成高品質人物和場景圖片

### 階段 3：靜態圖→動態影片
1. 使用 **MV_06** 的影片提示詞
2. 根據場景選擇合適的生影片模型：
   - **快速場景**：使用 Kling 或 Hailuo
   - **高潮部分**：使用 Seedance 2.0（最電影感）
3. 生成影片片段

---

## 📋 使用流程

### 🎬 生圖流程

**Step 1：準備提示詞**
```
來自 MV_02、MV_03 或其他 Skill 的中文或英文提示詞
```

**Step 2：選擇模型**
```
推薦：FLUX.1 Dev（最平衡）
或 Ideogram V3（有文字時）
```

**Step 3：設定參數**
```
- 尺寸：landscape_16_9（1024x576）推薦用於 MV
- 數量：1 張或多張進行對比
- 風格：在提示詞中明確指定
```

**Step 4：發起請求**
```bash
curl -s -X POST "https://fal.run/fal-ai/flux/dev" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "你的提示詞",
    "image_size": "landscape_16_9",
    "num_images": 1
  }'
```

**Step 5：下載圖片**
```bash
curl -s -o "output.jpg" "{返回的圖片 URL}"
```

---

### 🎥 生影片流程

**快速版（Kling/Hailuo）**
```bash
curl -s -X POST "https://fal.run/fal-ai/kling-video/v2.1/master/text-to-video" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "影片提示詞",
    "duration": 5,
    "model_name": "kling-v2.1"
  }'
```

**電影感版（Seedance 2.0）**
使用 Python 腳本（已包含在 `scripts/generate_video.py`）：
```bash
python scripts/generate_video.py \
  --prompt "你的影片提示詞" \
  --duration 8 \
  --model seedance2
```

---

## 💰 成本預估

### 典型 MV 製作成本

| 項目 | 數量 | 單價 | 總價 |
|------|------|------|------|
| 生圖（分鏡設計） | 9 張 | $0.025 | $0.23 |
| 生圖（額外角度） | 3 張 | $0.025 | $0.08 |
| 生影片（快速） | 3 段 × 5秒 | $0.07 | $1.05 |
| 生影片（電影感） | 2 段 × 8秒 | $0.20 | $3.20 |
| **總計** | - | - | **~$4.56** |

💡 提示：使用 FLUX Schnell 可進一步降低成本，但品質會下降。

---

## 🎯 最佳實踐

✅ **圖片生成**
- 使用詳細的英文提示詞（中文也可但英文更精確）
- FLUX.1 Dev 是最佳的成本效益選擇
- 先生 1-2 張測試，滿意再批量生成

✅ **影片生成**
- 短視頻（5秒）用 Kling（最便宜）
- 中等視頻（6-8秒）用 Hailuo（電影感）
- 高潮片段用 Seedance 2.0（最高品質）
- 提示詞要詳細描述鏡頭運動和時間進度

✅ **成本優化**
- 不是每段都要用 Seedance（預算有限時）
- Kling 的效果其實已經很好，適合大多數場景
- 保留 Seedance 給 MV 高潮部分

✅ **質量保證**
- 生成後檢查色彩、清晰度、人臉是否自然
- 如不滿意，調整提示詞重新生成（不額外計費，只計最後下載的）
- 下載高解析度版本以備後期編輯

---

## 📞 與 MV 工作流程的整合

**使用順序**：
1. ✅ **MV_01** → 創作歌詞（獲得 SUNO 風格）
2. 🎵 **ai-media-generator** → 用 SUNO 生成音樂
3. ✅ **MV_02** → 設計角色（獲得提示詞）
4. 🎨 **ai-media-generator** → 生圖確認角色外觀
5. ✅ **MV_03~06** → 完成所有視覺和影片提示詞
6. 🎬 **ai-media-generator** → 批量生成所有圖片和影片
7. ✅ **yt-auto-publisher** → 上傳到 YouTube

---

## 🔗 相關工具

- **SUNO**（音樂生成）：使用 SUNO 官網，MV_01 提供風格描述
- **FAL 平台**（圖片/影片生成）：本 Skill 的技術基礎
- **Dreamina**（Seedance 2.0）：用於高品質影片生成

---

## ❓ 常見問題

**Q: FLUX.1 和 Ideogram 如何選擇？**
A: 默認用 FLUX.1 Dev（品質平衡），有文字時用 Ideogram V3。

**Q: 生影片什麼時候用 Kling，什麼時候用 Seedance？**
A: Kling 用於快速場景和對話，Seedance 用於高潮和特效鏡頭。

**Q: 如果對生成結果不滿意？**
A: 調整提示詞後重新生成，不收取額外費用。已下載的圖片才計費。

**Q: 支援中文提示詞嗎？**
A: 支援，但英文更精確。建議重要場景用英文提示詞。

---

準備好生成你的 MV 素材了嗎？使用 MV 工作流程配合本工具！🎨🎬✨
