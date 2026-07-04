---
name: ai-media-generator
description: >
  AI 多媒體生成器 — 生成圖片和影片。按量計費、無月費。
  生圖：FLUX.1 Dev/Pro（$0.03/張）、Ideogram V3。
  生影片（快速省錢）：Kling V2.1（$0.07/秒）、Hailuo（$0.28/6秒）、Wan 2.1。
  生影片（高品質電影感）：Dreamina Seedance 2.0（$0.15~0.30/秒）。
  讀圖/OCR：使用 Claude 內建視覺能力或 Gemini Vision（免費）。
  觸發：「生圖」「生成圖片」「畫一張」「AI 繪圖」「text to image」
  「生影片」「生成影片」「AI 影片」「text to video」「做動畫」「Dreamina」
  「image generation」「video generation」「高品質影片」「電影感影片」
author: 阿亮老師・3A科技研究社
version: 2.0.0
tags: [生圖, 生影片, AI繪圖, FLUX, Kling, Hailuo, Dreamina, Seedance, 圖片生成, 影片生成]
---

# AI 多媒體生成器

> 按量計費，用多少付多少。生圖 $0.03/張，生影片 $0.07/秒。

## 環境需求

- 環境變數 `FAL_KEY` 已設定（Windows 使用者環境變數）
- curl（已內建）

## 生圖（Text-to-Image）

### 可用模型

| 模型 | Endpoint | 價格 | 適用場景 |
|:---|:---|:---:|:---|
| FLUX.1 Dev | `fal-ai/flux/dev` | ~$0.025/張 | 通用、高品質（推薦） |
| FLUX.1 Pro | `fal-ai/flux-pro/v1.1` | ~$0.05/張 | 最高品質 |
| FLUX.1 Schnell | `fal-ai/flux/schnell` | ~$0.003/張 | 快速草稿、最便宜 |
| Ideogram V3 | `fal-ai/ideogram/v3` | $0.03~0.09/張 | 文字渲染強 |
| Recraft V3 | `fal-ai/recraft-v3` | ~$0.04/張 | 設計風格 |

### 呼叫方式（同步）

```bash
curl -s -X POST "https://fal.run/{MODEL_ENDPOINT}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "你的提示詞（英文效果最好）",
    "image_size": "landscape_16_9",
    "num_images": 1
  }'
```

### image_size 選項

| 值 | 尺寸 |
|:---|:---|
| `square` | 1024x1024 |
| `square_hd` | 1536x1536 |
| `landscape_4_3` | 1024x768 |
| `landscape_16_9` | 1024x576 |
| `portrait_4_3` | 768x1024 |
| `portrait_16_9` | 576x1024 |

### 回應格式

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/...",
      "width": 1024,
      "height": 576,
      "content_type": "image/jpeg"
    }
  ],
  "seed": 12345,
  "prompt": "..."
}
```

### 圖片下載

```bash
curl -s -o "output.jpg" "{IMAGE_URL}"
```

## 生影片（Text-to-Video）

### 可用模型

#### 快速省錢（curl 同步呼叫）

| 模型 | Endpoint | 價格 | 說明 |
|:---|:---|:---:|:---|
| Kling V2.1 Master | `fal-ai/kling-video/v2.1/master/text-to-video` | ~$0.07/秒 | 人臉表情最強 |
| Hailuo 2.3 | `fal-ai/minimax-video/hailuo-ai-video-01-director/text-to-video` | ~$0.28/6秒 | 電影感 |
| Wan 2.1 | `fal-ai/wan/v2.1/text-to-video` | ~$0.10/秒 | 便宜 |

#### 高品質電影感 — Dreamina Seedance 2.0（Python 腳本輪詢）

| 模型 | 解析度 | 價格 | 說明 |
|:---|:---:|:---:|:---|
| Seedance 2.0 標準 | 720p | ~$0.30/秒 | 最高品質 |
| Seedance 2.0 Fast | 720p | ~$0.15/秒 | 快速草稿 |
| Seedance 2.0 標準 | 1080p | ~$0.60/秒 | 頂級品質 |

> 詳細定價與省錢技巧見 `references/pricing.md`  
> Prompt 寫作指南（cinematic 關鍵字）見 `references/prompt-guide.md`

### 呼叫方式 A：curl 同步（Kling / Hailuo / Wan）

```bash
curl -s -X POST "https://fal.run/{MODEL_ENDPOINT}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "描述影片內容（英文）",
    "duration": "5",
    "aspect_ratio": "16:9"
  }'
```

### 呼叫方式 B：Python 腳本（Dreamina Seedance 2.0）

```bash
python scripts/generate_video.py \
  --prompt "完整英文提示詞" \
  --duration 5 \
  --resolution 720p \
  --aspect_ratio 16:9 \
  --model seedance-2.0 \
  --output ./videos/
```

> ⚠️ 使用 Dreamina 前務必告知使用者費用，確認後再執行。

### 回應格式

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/...",
    "content_type": "video/mp4"
  }
}
```

### 影片下載

```bash
curl -s -o "output.mp4" "{VIDEO_URL}"
```

## 圖片轉影片（Image-to-Video）

```bash
curl -s -X POST "https://fal.run/fal-ai/kling-video/v2.1/master/image-to-video" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "the cat starts walking",
    "image_url": "https://...",
    "duration": "5",
    "aspect_ratio": "16:9"
  }'
```

## 讀圖 / OCR

不需要額外 API。使用以下方式：
1. **Claude Code 內建**：直接在對話中提供圖片路徑，Claude 可以直接讀取和分析圖片
2. **Gemini Vision**：使用者已有 Gemini API Key，可透過 Gemini 的多模態功能免費讀圖

## 工作流程

### 使用者說「生圖」時：
1. 確認 `FAL_KEY` 環境變數存在
2. 將中文提示詞翻譯為英文（效果更好）
3. 選擇適合的模型（預設 FLUX.1 Dev）
4. 用 curl 同步呼叫 `https://fal.run/{endpoint}`
5. 從回應取得圖片 URL
6. 用 curl 下載到本地
7. 用 Read 工具展示圖片給使用者

### 使用者說「生影片」時：
1. 確認 `FAL_KEY` 環境變數存在
2. 將中文提示詞翻譯為英文
3. 提醒使用者影片會花費 $0.07~0.28（確認後再執行）
4. 用 curl 同步呼叫影片端點（可能需要較長等待時間）
5. 下載影片到本地

## 注意事項

- 提示詞用**英文**效果最好，中文會自動翻譯但品質可能下降
- 生影片比生圖貴很多，執行前先確認使用者意願
- 圖片 URL 是暫時的，務必下載到本地保存
- 帳戶餘額可在 https://fal.ai/dashboard 查看
