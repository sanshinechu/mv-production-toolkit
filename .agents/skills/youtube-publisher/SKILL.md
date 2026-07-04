---
name: YouTube 自動發布工具
description: 自動上傳影片到 YouTube、管理頻道、批次上傳。支援 YouTube Data API v3 和瀏覽器自動化
triggers: 上傳 YouTube、YouTube 發布、上傳影片、發布到 YouTube、YouTube upload、影片上傳、批次上傳
version: 2.0.0
author: 阿亮老師・3A科技研究社
---

## 📤 功能說明

全自動 YouTube 影片發布工具，可以：
- ✅ **單支上傳**：快速上傳單支影片到 YouTube
- ✅ **批次上傳**：用 CSV 檔案一次上傳多支影片
- ✅ **頻道管理**：管理播放清單、更新頻道資訊、查看分析
- ✅ **中繼資料設定**：自動填寫標題、描述、標籤、分類
- ✅ **隱私設定**：自動設為公開/非公開/限制分享
- ✅ **備援方案**：如無法設定 API，可用瀏覽器自動化

---

## 🚀 快速開始

### 前置檢查（每次使用前）

```bash
# 檢查 Python 環境
python --version

# 驗證 YouTube 認證
python scripts/setup_credentials.py --verify

# 檢查所有依賴和配置
python scripts/env_check.py
```

### 三種上傳方式

| 方式 | 適用場景 | 所需時間 | 難度 |
|------|--------|--------|------|
| **單支上傳** | 1-2 支影片 | 2-3 分鐘 | ⭐ 簡單 |
| **批次上傳** | 多支影片（10+） | 5-10 分鐘 | ⭐⭐ 中等 |
| **頻道管理** | 修改頻道、播放清單 | 1-2 分鐘 | ⭐⭐⭐ 複雜 |

---

## 🔐 認證設定（首次使用）

### Step 1：設定 Google Cloud 專案
1. 訪問 [Google Cloud Console](https://console.cloud.google.com)
2. 建立新專案或使用現有專案
3. 啟用 **YouTube Data API v3**
4. 建立 **OAuth 2.0 用戶端 ID**（Desktop 應用程式）
5. 下載 JSON 憑證到 `credentials/client_secrets.json`

> 詳見 `references/google_api_setup.md` 中的圖文說明

### Step 2：初始化認證
```bash
python scripts/setup_credentials.py
```
首次執行會要求你授權，之後自動保存 token 供後續使用。

### Step 3：驗證認證
```bash
python scripts/setup_credentials.py --verify
```
應該顯示你的頻道名稱，表示認證成功。

---

## 📋 使用方法

### 方法 A：單支上傳

最簡單的方式，適合偶爾上傳一支影片。

```bash
python scripts/upload_video.py \
  --file "/path/to/video.mp4" \
  --title "我的 MV 標題" \
  --description "MV 描述文字" \
  --tags "MV,音樂,藝術" \
  --privacy "public"
```

**參數說明**：
- `--file`：影片檔案路徑（必需）
- `--title`：影片標題
- `--description`：詳細描述（可包含 YouTube 連結、參考資料等）
- `--tags`：標籤（逗號分隔）
- `--privacy`：`public`（公開）、`unlisted`（不公開）、`private`（私密）
- `--category`：分類（預設 `Music`）
- `--thumbnail`：自訂封面圖片路徑

**完整範例**：
```bash
python scripts/upload_video.py \
  --file "C:/Users/user/Videos/my_mv.mp4" \
  --title "【官方 MV】我的創作歌曲" \
  --description """
  我的新歌 MV 首映！
  
  🎵 原創音樂
  🎬 MV 製作：AI 生成
  
  歌詞由 Codex 創作
  影片由 Dreamina 生成
  
  ► 在 Spotify 聆聽：[連結]
  ► 更多作品：[頻道連結]
  
  感謝觀看！❤️
  """ \
  --tags "原創音樂,MV,AI生成,Scratch音樂,教育" \
  --privacy "public" \
  --thumbnail "cover.jpg"
```

---

### 方法 B：批次上傳

一次上傳多支影片，最適合發布整個 MV 系列。

**Step 1：準備 CSV 檔案** (`videos.csv`)
```csv
file,title,description,tags,privacy,category
/path/to/video1.mp4,MV 第一集,描述1,tag1;tag2,public,Music
/path/to/video2.mp4,MV 第二集,描述2,tag1;tag2,public,Music
/path/to/video3.mp4,MV 第三集,描述3,tag1;tag2,public,Music
```

**Step 2：執行批次上傳**
```bash
python scripts/batch_upload.py --csv videos.csv
```

**CSV 欄位說明**：
- `file`：影片檔案路徑（必需）
- `title`：影片標題
- `description`：影片描述
- `tags`：標籤（用 `;` 分隔）
- `privacy`：隱私設定
- `category`：分類（預設 Music）
- `thumbnail`：封面圖片路徑（可選）

**高級選項**：
```bash
python scripts/batch_upload.py \
  --csv videos.csv \
  --playlist "我的 MV 系列" \
  --delay 30  # 每支之間延遲 30 秒
```

---

### 方法 C：頻道管理

管理播放清單、更新頻道資訊、檢查分析。

**建立或更新播放清單**：
```bash
python scripts/manage_channel.py \
  --action create_playlist \
  --playlist_title "我的 MV 合集" \
  --playlist_desc "所有官方 MV"
```

**將影片添加到播放清單**：
```bash
python scripts/manage_channel.py \
  --action add_to_playlist \
  --playlist_id "PLxx..." \
  --video_id "dQw4w9WgXcQ"
```

**查看頻道分析**：
```bash
python scripts/manage_channel.py \
  --action get_analytics \
  --days 30  # 最近 30 天
```

---

## 💡 在 MV 製作流程中的應用

### 完整發布流程

```
MV_01-10 製作完成
    ↓
ai-media-generator 生成最終影片
    ↓
使用本工具上傳 YouTube
    ↓
設定標題、描述、標籤、封面
    ↓
建立播放清單（如有多支 MV）
    ↓
分享 YouTube 連結
```

### 建議的影片描述模板

```
【官方 MV】《歌曲名稱》

🎵 原創音樂
🎬 MV 製作：AI 生成（Dreamina Seedance 2.0）

【歌詞創作】
歌詞由 Codex AI 根據主題創作

【角色設計】
主角由 AI 根據曲風設計（FLUX.1 Dev 生成）

【視覺製作】
- 場景設計：AI 影像生成
- 分鏡設計：AI 九宮格設計
- 運鏡效果：AI 動畫生成

【技術棧】
- 詞曲：Codex + SUNO
- 視覺：FLUX.1 + Dreamina
- 發布：自動化 YouTube 上傳

【觀看完整製作流程】
羅東國小資訊組長 - MV 製作工作流程
YouTube 頻道：[頻道連結]

感謝觀看！如喜歡請按讚、訂閱、打開通知鈴！🔔❤️

【標籤】
#原創音樂 #MV #AI生成 #Scratch音樂教育 #創意製作
```

---

## 📊 API 配額管理

### 配額消耗表

| 操作 | 配額 | 每日上限 |
|------|------|---------|
| 上傳影片 (videos.insert) | 1600 | 約 6 支 |
| 更新中繼資料 (videos.update) | 50 | 約 200 次 |
| 建立播放清單 | 50 | 約 200 次 |
| 查詢分析 | 100 | 約 100 次 |

> ⚠️ YouTube Data API v3 每日免費配額為 **10,000 單位**
> 一支影片上傳消耗 1600 單位，所以每天最多上傳 6 支

**配額檢查**：
```bash
python scripts/env_check.py --quota
```

---

## 🔄 錯誤處理和備援

### 如果 API 失敗

自動切換到瀏覽器自動化：
```bash
python scripts/upload_video.py \
  --file "video.mp4" \
  --title "標題" \
  --use_browser  # 強制使用瀏覽器
```

### 常見錯誤

| 錯誤 | 原因 | 解決方案 |
|------|------|---------|
| `Invalid client` | 憑證錯誤 | 重新執行 `setup_credentials.py` |
| `Rate limit exceeded` | 超過配額 | 等待 24 小時或購買 API 額度 |
| `Video format not supported` | 格式不支援 | 轉換為 MP4 格式 |
| `File too large` | 檔案過大 | 壓縮影片或分割上傳 |

---

## 💰 成本

- ✅ **YouTube Data API**：免費（有日配額限制）
- ✅ **此工具**：開源免費
- ❌ 需要費用：購買額外的 API 配額（如超過每日限制）

---

## 🎯 最佳實踐

✅ **上傳前準備**
- 準備高品質的 MP4 影片（至少 1080p）
- 準備吸睛的封面圖片（1280x720 推薦）
- 撰寫詳細、有 SEO 的描述
- 設定相關標籤

✅ **批次上傳**
- 測試單支上傳成功後再進行批次
- 使用 `--delay` 參數避免觸發頻率限制
- 保存 CSV 檔案供下次更新使用

✅ **頻道管理**
- 建立合理的播放清單分類
- 定期檢查分析，優化上傳時間
- 保持頻道資訊完整和專業

✅ **發布策略**
- 週末或晚間上傳（觀看人數高峰）
- 設為「不公開」先檢查，滿意後改「公開」
- 上傳完成後分享到社群媒體

---

## 📞 與 MV 工作流程的整合

**最後一步**：
1. ✅ **ai-media-generator** → 生成最終影片
2. 📤 **本工具** → 自動上傳到 YouTube
3. 🔔 → 分享連結到社群媒體

---

準備好發布你的 MV 到 YouTube 了嗎？讓自動化工具為你處理繁瑣的上傳步驟！🚀✨
