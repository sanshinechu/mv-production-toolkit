---
name: mv-production-packaging
description: MV 製作完整工作流總控技能。當使用者要求完成一個 MV 製作（從歌詞創作到 YouTube 發布）、一次跑完整個製作線、或說「使用 mv-production-packaging」時使用。此技能整合 11 個製作步驟，包括歌詞創作、角色設計、場景提示詞、分鏡設計、視頻生成、組裝驗證、YouTube 上傳。適用於 Codex 和 Codex 的雙 AI 協作模式。
---

# MV 製作完整工作流 - 生產總控

## 先讀

- `HANDOFF.md` — 所有交接信息與中央進度追蹤
- `MV製作進度追蹤.md` — 詳細的進度表與問題紀錄
- `AGENTS.md` — 專案方針與語言規範
- 歌詞與風格描述（見 HANDOFF.md）
- 主角一致性參考詞（女+男，見 HANDOFF.md）

---

## 流程概覽（11 個步驟）

| 步驟 | 名稱 | 負責 | 時間 | 狀態 |
|------|------|------|------|------|
| 1️⃣ | MV_01：歌詞創作 + SUNO 風格 | Codex | 30-45 分 | ✅ 完成 |
| 2️⃣ | SUNO 音樂生成 | 外部（SUNO） | 30-60 分 | ✅ 完成 |
| 3️⃣ | MV_02：主角設計（女+男） | Codex | 15-30 分 | ✅ 完成 |
| 4️⃣ | MV_03：場景影像提示詞 | Codex | 30-40 分 | ✅ 完成 |
| 5️⃣ | MV_04：九宮格分鏡 | Codex + Codex | 20-30 分 設計 + 生圖 | ✅ 完成 |
| 6️⃣ | MV_05：截圖放大提質 | Codex + Codex | 10-15 分 | ✅ 完成 |
| 7️⃣ | MV_06：影片動態提示詞 | Codex | 20-30 分 | ✅ 完成 |
| 8️⃣ | 生圖 + 生影片 | Codex（media-generation） | 45-90 分 | 🔄 進行中 |
| 9️⃣ | FFmpeg 本地組裝 | Codex | 10-15 分 | ⬜ 待開始 |
| 🔟 | 本地播放驗證（VLC） | Codex | 10-15 分 | ⬜ 待開始 |
| 1️⃣1️⃣ | **YouTube 上傳**（使用 youtube_publisher） | Codex | 15-30 分 | ⬜ 待開始 |
| 1️⃣2️⃣ | **打包與資產整理** | Codex | 5-10 分 | ⬜ 待開始 |

---

## 關鍵概念

### 🎬 兩階段協作模式

**階段 1：設計階段（Codex 主導）**
- MV_01 歌詞創作
- MV_02 角色設計
- MV_03-06 視覺與動態提示詞設計
- 準備完整的提示詞與參考資源

**階段 2：生成與組裝階段（Codex 為主 + Codex 組裝驗證）**
- Codex 使用 `media-generation` skill 生成圖片與視頻
- Codex 用 FFmpeg 組裝、驗證、發布

### 🔗 中央檔案：HANDOFF.md

**HANDOFF.md 是生命線**，包含：
- 當前狀態與進度
- 所有已完成的提示詞
- 待執行的任務清單
- 每個階段的交接信息

**規則**：
- 每次工作前讀 HANDOFF.md 的「目前狀態」
- 每次工作結束前更新「下一步」與完成項目
- 假設下一個接手者是陌生人

---

## 完整流程詳解

### 步驟 1️⃣-3️⃣：概念 + 設計（30-90 分）

#### 1. MV_01：歌詞創作 + SUNO 風格

**輸入**：
- 主題（例：「初戀在咖啡廳」）
- 曲風（例：R&B/Soul）
- 情感基調（例：溫暖、甜蜜）

**工作內容**：
- 使用 `mv-01-lyric-songwriting` skill
- 創作版權友好的完整歌詞（含結構標籤：Verse/Chorus/Bridge/Outro）
- 撰寫英文 SUNO Style 描述（節奏、樂器、情緒）

**輸出**：
```
✅ 完整歌詞（繁體中文，帶結構標籤）
✅ SUNO 英文風格描述
✅ 記錄到 HANDOFF.md
```

**驗證檢查**：
- [ ] 歌詞無低俗或版權問題
- [ ] 結構標籤完整（至少 Verse × 2、Chorus、Bridge、Outro）
- [ ] SUNO Style 用英文撰寫，描述清晰

#### 2. 外部：SUNO 音樂生成

**負責人**：使用者（或 Codex 用瀏覽器協助）

**步驟**：
- 到 `https://suno.ai/`
- 複製 Step 1 的歌詞與 Style 描述
- 生成 MP3 檔案
- 下載到 `outputs/` 資料夾，命名為 `<歌名>.mp3`

**預期結果**：
- 一個 MP3 檔案，時長通常 3-4 分鐘
- 記錄實際時長（例：216.4 秒）

#### 3. MV_02：主角設計（女+男）

**輸入**：
- 曲風 + 歌詞內容
- 性別與氣質需求

**工作內容**：
- 使用 `mv-02-character-design` skill（分別為女主角與男主角執行）
- 設計 Split Screen 格式的人物形象
  - 左側：臉部特寫肖像（Close-up Portrait）
  - 右側：全身照（Full-body Shot）
- 生成英文影像提示詞 + 中文翻譯

**輸出**：
```
✅ 女主角英文提示詞 + 中文描述
✅ 男主角英文提示詞 + 中文描述
✅ 女主角一致性參考詞（貼在後續所有生圖提示詞開頭）
✅ 男主角一致性參考詞（同上）
✅ 記錄到 HANDOFF.md
```

**一致性參考詞格式**：
```
[FEMALE_CHARACTER] East Asian woman, 長直黑髮, 米色毛衣, 
溫柔甜蜜, consistent character appearance throughout all shots
```

---

### 步驟 4️⃣-7️⃣：視覺設計（120-160 分）

#### 4. MV_03：場景影像提示詞

**輸入**：
- 歌詞內容（分段落）
- 主角一致性參考詞 × 2

**工作內容**：
- 使用 `mv-03-image-prompt-generation` skill
- 為歌曲的主要段落（通常 2-3 個）設計場景提示詞
- 含詳細描述：主題、構圖、光線、氛圍、風格

**輸出**：
```
✅ 場景 1 提示詞（Verse）
✅ 場景 2 提示詞（Chorus）  
✅ 場景 3 提示詞（Bridge）
✅ 記錄到 HANDOFF.md
```

#### 5. MV_04：九宮格分鏡設計

**工作流程**：

a. **設計階段（Codex）**
   - 使用 `mv-04-nine-grid-storyboard` skill
   - 設計 9 張多角度分鏡圖的提示詞
   - 涵蓋遠景、中景、特寫、仰視、俯視等多樣鏡頭

b. **生成階段（Codex）**
   - 使用 `media-generation` skill（FLUX.1 Dev）
   - 生成 5016×5016 PNG（9 宮格）
   - 品質設定：high / very_high

**輸出**：
```
✅ 九宮格提示詞（中文）
✅ 九宮格圖片（5016×5016 PNG）
✅ 記錄到 HANDOFF.md
```

#### 6. MV_05：截圖放大提質

**工作流程**：

a. **策略階段（Codex）**
   - 從九宮格中選 2-3 張重點格子
   - 設計放大至 1672×1672 的提示詞

b. **生成階段（Codex）**
   - 使用 `media-generation` skill
   - 生成高解析度版本（1672×1672 PNG）

**輸出**：
```
✅ 放大提質提示詞 × 2-3
✅ 高解析度圖片 × 2-3（1672×1672 PNG）
✅ 記錄到 HANDOFF.md
```

#### 7. MV_06：影片動態提示詞

**輸入**：
- 九宮格圖片（或放大版）
- 對應的歌詞段落

**工作內容**：
- 使用 `mv-06-video-prompt-generation` skill
- 為靜態圖片添加動態描述
- 含：角色動作、表情變化、環境氛圍、運鏡方式

**輸出**：
```
✅ 影片段 1 提示詞（Verse）
✅ 影片段 2 提示詞（Chorus）
✅ 影片段 3 提示詞（Bridge）
✅ ...（依照歌詞結構）
✅ 記錄到 HANDOFF.md
```

---

### 步驟 8️⃣：生圖 + 生影片（60-120 分）

**負責人**：Codex（使用 `media-generation` skill）

**工作內容**：

a. **生成靜態圖片**
   - 女主角設計圖（Split Screen）
   - 男主角設計圖（Split Screen）
   - 九宮格分鏡圖
   - 放大提質圖片

b. **生成影片段**
   - 根據完整歌曲結構生成 6+ 個視頻段
   - 重點：**時長必須精確匹配歌詞結構**
   - 例：
     ```
     Verse 1 → 30 秒
     Pre-Chorus → 20 秒
     Chorus → 30 秒
     Verse 2 → 30 秒
     Bridge → 30 秒
     Outro → 16 秒
     ────────────────
     總計 → 3:36（與音樂同步）
     ```

**生成參數**：
```
模型：FLUX.1 Dev（生圖） / Kling V2.1 或 Hailuo（生影片）
解析度：1920×1080（影片） / 1024×1024（靜態圖）
幀率：24-30 fps
格式：MP4 / PNG
成本預估：$15-30 USD
```

**輸出**：
```
✅ 靜態圖片：character 資料夾內
✅ 視頻段 × 6+：videos_v2 資料夾內
✅ 時長驗證清單（每個視頻段的實際時長）
✅ 回傳 Codex，準備組裝
```

**關鍵驗證**：
- [ ] 每個視頻段的時長是否精確？
- [ ] 總長是否等於 SUNO 音樂長度？
- [ ] 解析度是否符合（1920×1080）？
- [ ] 人物一致性是否延續？

---

### 步驟 9️⃣：FFmpeg 本地組裝（10-15 分）

**負責人**：Codex

**前置檢查**：
```bash
# 確認 FFmpeg 可用
ffmpeg -version 2>&1 | head -1

# 確認音樂與視頻檔案存在
ls -lh outputs/*.mp3
ls -lh outputs/videos_v2/*.mp4
```

**組裝步驟**：

a. **創建視頻列表（concat_list.txt）**
   ```
   file '01_Verse1.mp4'
   file '02_PreChorus.mp4'
   file '03_Chorus.mp4'
   file '04_Verse2.mp4'
   file '05_Bridge.mp4'
   file '06_Outro.mp4'
   ```

b. **合併視頻段**
   ```bash
   ffmpeg -f concat -safe 0 -i concat_list.txt \
     -c:v libx264 -c:a aac -shortest \
     merged_video.mp4
   ```

c. **合併音樂 + 視頻**
   ```bash
   ffmpeg -i 因你而轉動.mp3 -i merged_video.mp4 \
     -c:v libx264 -c:a aac -pix_fmt yuv420p \
     -shortest \
     最終_完整MV_$(date +%Y-%m-%d).mp4
   ```

   **關鍵參數**：
   - `-shortest`：輸出時長 = min(音樂, 視頻)
   - `-pix_fmt yuv420p`：確保 YouTube 相容
   - `-c:a aac -b:a 128k`：音頻品質

d. **移動到 outputs/final/**
   ```bash
   mkdir -p outputs/final
   mv 最終_完整MV_*.mp4 outputs/final/
   ```

**輸出**：
```
✅ 完整 MV 檔案：outputs/final/<名稱>.mp4
✅ 驗證時長是否符合預期
✅ 記錄到 HANDOFF.md
```

**常見問題排查**：
- 視頻段總長 < 音樂長度 → 需要重新生成更長的視頻
- 音畫不同步 → 檢查 FFmpeg 合併參數
- 色彩偏差 → 檢查生圖解析度和編碼設定

---

### 步驟 🔟：本地播放驗證（VLC）（10-15 分）

**負責人**：Codex

**工作內容**：

a. **開啟 VLC 播放器**
   ```bash
   # Windows
   "C:\Program Files\VideoLAN\VLC\vlc.exe" "outputs/final/MV.mp4"
   ```

b. **驗證清單**
   - [ ] 音視頻同步（聲音與嘴型對齐）
   - [ ] 色彩準確度（膚色、衣服顏色是否正確）
   - [ ] 解析度與清晰度（1920×1080 Full HD）
   - [ ] 音量與音質（無爆音、清晰度適當）
   - [ ] 場景轉換平滑（無突兀卡頓）
   - [ ] 字幕對齐（如有字幕）
   - [ ] 完整播放時長（驗證總長度）

c. **記錄截圖**（可選）
   - 拍 3-5 個關鍵幀的截圖
   - 記錄到 outputs/final/validation_screenshots/

**輸出**：
```
✅ 本地播放驗證通過
✅ 驗證報告（含截圖路徑）
✅ 確認可上傳 YouTube
✅ 記錄到 HANDOFF.md
```

**若驗證失敗**：
- 音視頻不同步 → 回到步驟 9，調整 FFmpeg 參數
- 色彩不符 → 回到步驟 8，檢查生圖設定
- 時長錯誤 → 回到步驟 8，重新生成視頻段

---

### 步驟 1️⃣1️⃣：YouTube 上傳（使用 youtube_publisher）（15-30 分）

**負責人**：Codex（使用 youtube_publisher skill）

**前置準備**：
- FFmpeg 組裝完成，最終 MV 檔案位於 `outputs/final/`
- 標題、描述、標籤、關鍵詞已在 HANDOFF.md metadata 部分準備好
- YouTube 非公開測試頻道已設定並可用

**上傳方案（推薦使用 youtube_publisher）**：

#### 📋 方案 A：使用 youtube_publisher Skill（推薦）

**優點**：快速、自動化、精確控制、無需人工點擊

```bash
# 從 HANDOFF.md 提取以下資訊：
標題：見 metadata.title
描述：見 metadata.description
標籤：見 metadata.tags
頻道：測試頻道（非公開）
隱私級別：private（非公開）

# 執行 youtube_publisher
使用 youtube_publisher skill：
- 輸入檔案：outputs/final/<標題>_完整MV.mp4
- 標題：從 HANDOFF.md 複製
- 描述：從 HANDOFF.md 複製
- 標籤：從 HANDOFF.md 複製（逗號分隔）
- 隱私級別：private
- 頻道：測試頻道或指定頻道
```

**整合檢查清單**：
- [ ] MP4 檔案確實存在於 `outputs/final/`
- [ ] 檔案大小 > 10MB（確保完整）
- [ ] 從 HANDOFF.md 複製標題、描述、標籤
- [ ] youtube_publisher skill 已準備好
- [ ] 確認上傳到非公開頻道（privacy: private）

#### 📋 方案 B：人工 YouTube Studio 上傳（備選）

如果 youtube_publisher 遇到問題，使用人工上傳：

**步驟**：
1. 登入 YouTube Studio（https://studio.youtube.com）
2. 點擊「建立」→「上傳影片」
3. 上傳 MP4 檔案（`outputs/final/<標題>_完整MV.mp4`）
4. 填入詳細資訊：
   - **標題**：從 HANDOFF.md 複製
   - **描述**：從 HANDOFF.md 複製
   - **標籤**：從 HANDOFF.md 複製（逗號分隔）
   - **寬限年齡限制**：否（除非內容涉及敏感主題）
5. 選擇隱私級別：**非公開（Private）**
6. 點擊「排定」或「發布」
7. 等待處理完成（通常 5-15 分鐘）

**手動上傳檢查清單**：
- [ ] 檔案上傳進度條到 100%
- [ ] 等待處理完成（藍色「處理中」消失）
- [ ] 複製影片連結

---

**上傳後驗證（視頻處理完成後，15-30 分內）**：

完成後，執行完整驗證檢查清單：

```
🔍 影片處理與可用性
- [ ] 影片已完成上傳和處理（YouTube 後台不再顯示「處理中」）
- [ ] 影片狀態顯示為「非公開」（Private）
- [ ] 可複製公開/非公開連結

📺 影片品質與技術
- [ ] 解析度正確（1920×1080 Full HD 顯示）
- [ ] 幀率正確（24-30 fps）
- [ ] 位元率與品質良好（無明顯像素化）
- [ ] 無損壞或毛邊情況

🔊 音視頻同步與品質
- [ ] 音視頻同步準確（播放無延遲）
- [ ] 音量正常（非過大或過小）
- [ ] 無音頻失真或爆音
- [ ] 清晰度符合預期

🎨 視覺連續性與效果
- [ ] 場景轉換順暢（無跳幀）
- [ ] 顏色與光影連續
- [ ] 人物形象一致（無明顯風格變化）
- [ ] 運鏡流暢（無抖動或跳躍）

📋 元數據與互動
- [ ] 標題、描述、標籤正確顯示
- [ ] 播放清單已正確新增（如有）
- [ ] 縮圖正常顯示（首幀或自訂封面）
- [ ] 訂閱按鈕與互動按鈕可用

✅ 最終確認
- [ ] 複製最終 YouTube 連結
- [ ] 記錄上傳時間與視頻 ID
- [ ] 更新 HANDOFF.md 完成狀態
- [ ] 移動檔案至 outputs/final/completed（標記完成）
```

---

**輸出與記錄**：

```
✅ YouTube 非公開影片連結（格式：https://youtu.be/<視頻ID> 或非公開連結）
✅ 視頻 ID（YouTube URL 中的唯一識別碼）
✅ 上傳驗證報告（包含上述驗證清單的勾選狀態）
✅ 更新 HANDOFF.md：
   - 當前狀態 → 「✅ 已完成」
   - YouTube 連結 → 記錄最終連結
   - 完成時間 → 記錄上傳完成時間
   - 備註 → 任何問題與解決方案
```

---

**常見問題與解決方案**：

| 問題 | 原因 | 解決方案 |
|-----|------|--------|
| youtube_publisher 報錯 | YouTube API 配置或認證失敗 | 檢查 FAL_KEY / YouTube API 金鑰，重新認證 |
| 上傳卡住（進度條停止） | 網路連線中斷或檔案太大 | 檢查網路，確認 MP4 < 256GB，重試上傳 |
| 視頻處理超時 | YouTube 後台處理隊列繁忙 | 等待 1-2 小時，或更換時間重試 |
| 上傳後音畫不同步 | FFmpeg 組裝時使用了錯誤參數 | 回到步驟 9，檢查 FFmpeg 命令參數 |
| 顏色失真或解析度低 | 編碼器設定不當 | 回到步驟 8，確認生圖解析度 ≥ 1024×1024，生影片 ≥ 1920×1080 |

---

**整合 youtube_publisher 的優勢**：

```
✅ 速度：15-30 分完成（vs 人工上傳 5-10 分 + 等待處理 15-30 分 = 20-40 分）
✅ 精確：自動填入元數據，無誤輸入風險
✅ 可重複：同樣提示詞與參數可批量上傳多個 MV
✅ 驗證：支援自動驗證與錯誤報告
✅ 整合：直接與 HANDOFF.md 同步，無需人工轉抄
```

---

### 步驟 1️⃣2️⃣：打包與資產整理（5-10 分）

**負責人**：Codex

**工作目標**：
- 整理所有成品檔案到最終輸出資料夾
- 生成專業的 metadata.md（供 YouTube 和社群使用）
- 備份源素材與設計資料
- 生成完整檢查清單

---

#### 📦 **最終輸出結構**

```
outputs/<MV標題> [Codex]/
│
├── 🎬 核心檔案（必須）
│   ├── <MV標題>_完整MV.mp4          ← 最終影片（來自 Step 9）
│   ├── cover.png                     ← YouTube 封面（見下方）
│   └── metadata.md                   ← 完整 metadata（見範本）
│
├── 📄 參考檔案（可選但推薦）
│   ├── README.md                     ← 製作簡介與 YouTube 連結
│   └── CREDITS.md                    ← 製作團隊與工具名單
│
└── 📁 源素材備份（可選，保留工作痕跡）
    ├── characters/
    │   ├── female_character.png
    │   └── male_character.png
    ├── storyboards/
    │   └── mv04_9grid_storyboard.png
    └── videos_v2/
        ├── 01_Verse1_*.mp4
        ├── ... (等)
        └── 06_Outro_*.mp4
```

---

#### 🎨 **Step 12.1：生成封面圖（可選）**

**選項 A：截圖首幀（快速，5 分）**
```bash
# 使用 FFmpeg 截取 MP4 的第一幀作為封面
ffmpeg -i "outputs/final/<MV標題>_完整MV.mp4" \
  -ss 0 -vframes 1 -vf "scale=1920:1080" \
  "outputs/<MV標題> [Codex]/cover.png"
```

**選項 B：截取關鍵幀（推薦，10-15 分）**
```bash
# 截取視頻中最精彩的一幀（例如 30 秒位置）
ffmpeg -i "outputs/final/<MV標題>_完整MV.mp4" \
  -ss 00:00:30 -vframes 1 -vf "scale=1920:1080" \
  "outputs/<MV標題> [Codex]/cover.png"

# 或用 VLC 手動尋找最佳幀，截圖後儲存為 cover.png
```

**選項 C：AI 生成專業封面（可選，20-30 分）**

如需專業 YouTube 封面，使用 draw.py 或 media-generation：
- 參考剪片工作流的 `cover-image` skill
- 建立 `assets/style/` 目錄存放風格指南
- 參考 `assets/persona/` 中的主角形象照

---

#### 📋 **Step 12.2：撰寫 metadata.md（15-20 分）**

**快速開始**：
- 複製 `.Codex/skills/mv-production-packaging/metadata-template.md`
- 改名為 `metadata.md` 放到 `outputs/<MV標題> [Codex]/`
- 根據你的 MV 修改內容即可

**範本結構**（參考剪片工作流的 7 區塊）：

```markdown
# <MV標題> 完整元數據

## 📺 YouTube 描述

**開場（2-3 句）**
[闡述 MV 的核心價值與目標受眾]

示例：
「『初戀在咖啡廳』是一支溫暖甜蜜的 R&B/Soul MV，以年輕情侶在咖啡廳的初戀時光為主題。
透過精心設計的場景、人物造型與動感運鏡，呈現初戀的青春感與浪漫氛圍。」

**重點列表（用 ✅ 標記）**
- ✅ 曲風：R&B/Soul 溫暖成熟
- ✅ 主題：初戀、咖啡廳、年輕情侶
- ✅ 視覺風格：東亞美學、電影感光影
- ✅ 時長：3 分 36 秒

---

## 🎬 章節時間碼

用於 YouTube 章節標記，幫助觀眾快速導航：

```
0:00 Intro - 首次相遇的期待
0:30 Verse 1 - 女主角的心動時刻
1:00 Pre-Chorus - 眼神交匯
1:20 Chorus - 和你在一起
2:00 Verse 2 - 漫步夕陽
2:30 Bridge - 親密時刻
3:10 Outro - 永遠在一起
3:36 End
```

---

## 📱 社群版本

### Facebook（教師社群風格，可稍長）
[針對教師社群的貼文，強調製作流程或教學意義]

範例：
「✨ 新作品上架！『初戀在咖啡廳』MV 🎬

這支 MV 展示了從概念設計、角色設計、到完整影片生成的整個製作流程。
使用 AI 工具協助創意實現，證明了科技與藝術的完美結合。

影片特色：
🎥 電影感運鏡與場景設計
🎨 精心設計的人物造型
🎵 R&B/Soul 風格配樂

製作過程融合了 AI 生圖、視頻生成與傳統編輯技巧，
展示了新時代創作者的工作流程。

📺 完整影片：[YouTube 連結]
#MV #AudioVisual #AICreativity #Filmmaking」

### Instagram（短文 + 多 hashtag）
「🎬✨ 初戀在咖啡廳 MV 上架！

溫暖甜蜜的 R&B/Soul MV，
用鏡頭與光影述說年輕愛情的故事。

📹 現在觀看 →
#MusicVideo #RnB #Soul #Love #Cinematography #Aesthetic #MV #AudioVisual #FilmmakerLife #CreativeProcess #AIArt #NewMusic」

### Threads（共鳴型短句）
「新 MV 上線 🎬✨ 『初戀在咖啡廳』
用運鏡、光影、和音樂
講述初戀的甜蜜與悸動。
短短 3 分多，卻濃縮了青春的美好時刻。」

---

## 🔍 SEO 關鍵字

### 主關鍵字
- MV / Music Video
- R&B / Soul（曲風）
- 初戀 / 愛情（主題）

### 次關鍵字
- 電影感 MV
- 咖啡廳場景
- 年輕情侶
- 音樂製作

### 長尾關鍵字
- 「初戀在咖啡廳 MV」
- 「R&B Soul 愛情主題」
- 「高級感電影風格 MusicVideo」
- 「AI 生成視覺內容」

### 競品搜尋詞
[若有特定競品或參考作品，列出相關搜尋詞]

---

## 🏷️ YouTube 標籤（直接複製）

### 版本 A：按分類分組
```
MV,Music Video,R&B,Soul,Love,Romance,Indie Music,Original,Cinematography,Short Film
```

### 版本 B：按受眾分組
```
AudioVisual,MusicProduction,FilmMaking,CreativeProcess,IndieArtist,NewMusic
```

### 版本 C：**全部一次貼**（直接複製貼到 YouTube 標籤欄）
```
MV,Music Video,R&B,Soul,Love,Romance,Indie Music,Original,Cinematography,Short Film,AudioVisual,MusicProduction,FilmMaking,CreativeProcess,IndieArtist,NewMusic,初戀,咖啡廳,情侶,電影感
```

---

## ✅ 上架前檢查清單

- [ ] **標題**：簡潔、含主關鍵字
- [ ] **封面**：視覺吸引、人物清晰、1920×1080 解析度
- [ ] **字幕**：若有，時間碼準確（或啟用 YouTube 自動字幕）
- [ ] **描述前 100 字**：包含主關鍵字與 MV 核心資訊
- [ ] **章節時間碼**：按歌曲結構標記（可選但推薦）
- [ ] **標籤**：用「全部一次貼」版本（限 30 個，YouTube 會自動精簡）
- [ ] **播放清單**：若有系列 MV，加入對應播放清單
- [ ] **社群同步**：Facebook / Instagram / Threads 同時發佈
- [ ] **分享連結**：複製 YouTube 連結到 HANDOFF.md

---
```

---

#### 📄 **Step 12.3：撰寫 README.md（製作簡介，5 分）**

在 `outputs/<MV標題> [Codex]/` 中建立 README.md，簡述製作過程與觀看指南：

```markdown
# <MV標題> — 製作簡介

## 🎬 影片資訊

| 項目 | 內容 |
|------|------|
| **標題** | <MV標題> |
| **時長** | 3 分 36 秒 |
| **曲風** | R&B/Soul |
| **主題** | 初戀、咖啡廳、年輕情侶 |
| **YouTube 連結** | [連結] |
| **上線日期** | 2026-05-23 |

## 🎨 製作過程

此 MV 採用 **完整 AI 協作流程** 製作：

1. **歌詞創作** — 版權友好版本，適合 SUNO 生成音樂
2. **視覺設計** — 主角造型、場景提示詞、分鏡規劃
3. **素材生成** — FLUX.1 生圖、Kling V2.1 生視頻
4. **本地組裝** — FFmpeg 合併音樂與視頻段
5. **品質驗證** — VLC 本地播放確認
6. **YouTube 發布** — youtube_publisher 自動上傳

**製作時長**：約 6-8 小時（含 AI 等待時間）  
**技術棧**：Codex + Codex + SUNO + FAL.ai + FFmpeg

## 📁 檔案說明

- `<MV標題>_完整MV.mp4` — 完整 MV 影片檔
- `cover.png` — YouTube 封面圖（1920×1080）
- `metadata.md` — YouTube 描述、章節、社群、SEO、標籤
- `README.md` — 此檔案

## 🔗 快速連結

- 📺 [在 YouTube 觀看](https://youtu.be/...)
- 📝 完整 metadata 見 `metadata.md`
- 🎵 SUNO 音樂原始連結：[連結]（如公開）

---

**製作者**：[資訊組長姓名]  
**使用工具**：mv-production-packaging Skill  
**最後更新**：2026-05-23
```

---

#### ✅ **Step 12.4：最終檢查清單**

完成所有步驟後，逐項確認：

```
📦 輸出資料夾結構
- [ ] 資料夾名稱：outputs/<MV標題> [Codex]/
- [ ] 資料夾路徑正確，無 Windows 非法字元

🎬 核心檔案（三必須）
- [ ] <MV標題>_完整MV.mp4 存在且可播放
- [ ] cover.png 存在，解析度 1920×1080，視覺清晰
- [ ] metadata.md 存在且內容完整（7 區塊齊全）

📄 參考檔案（推薦）
- [ ] README.md 存在，包含製作簡介與 YouTube 連結
- [ ] CREDITS.md 存在（列出製作團隊與使用工具）

🎨 內容質量
- [ ] MP4 音視頻同步，無抖動或卡頓
- [ ] cover.png 人物形象清晰、色彩鮮豔
- [ ] metadata.md 格式規範、無排版錯誤
- [ ] YouTube 描述前 100 字含主關鍵字

🔗 外部連結
- [ ] YouTube 連結已複製到 HANDOFF.md
- [ ] YouTube 標籤已套用「全部一次貼」版本
- [ ] 社群貼文已排期發佈（FB / IG / Threads）

📝 交接與追蹤
- [ ] 更新 HANDOFF.md：「✅ 已完成」
- [ ] 記錄 YouTube 視頻 ID 與連結
- [ ] 記錄上傳時間與觀看統計（如有）

```

---

#### 🎯 **輸出物總結**

完成後的資料夾應包含：

```
✅ <MV標題>_完整MV.mp4     — YouTube 成品
✅ cover.png               — 專業封面圖
✅ metadata.md             — 7 區塊完整元數據
✅ README.md               — 製作簡介
✅ CREDITS.md              — 工具與團隊名單（可選）

+ 源素材備份（可選）
  ├── characters/          — 主角設計圖
  ├── storyboards/         — 九宮格與細節圖
  └── videos_v2/           — 各視頻段
```

---

**全部打勾 ✅ 即可視為整個 MV 製作流程完成！** 🎬✨

---

## 關鍵資源與工具

### 🔧 使用的 Skills

| Skill | 用途 |
|-------|------|
| `mv-01-lyric-songwriting` | 創作歌詞 + SUNO 風格 |
| `mv-02-character-design` | 設計主角（女+男） |
| `mv-03-image-prompt-generation` | 場景視覺提示詞 |
| `mv-04-nine-grid-storyboard` | 九宮格分鏡 |
| `mv-05-crop-and-upscale` | 截圖放大提質 |
| `mv-06-video-prompt-generation` | 影片動態提示詞 |
| `media-generation` | 生圖 + 生影片（Codex） |
| `youtube-publisher` | YouTube 上傳 |

### 📄 關鍵檔案

```
MV製作/
├── HANDOFF.md                    # 🔴 中央檔案，所有交接信息
├── AGENTS.md                     # 專案方針
├── MV製作進度追蹤.md            # 詳細進度表
│
├── outputs/
│   ├── <歌名>.mp3                # 音樂檔案
│   ├── characters/               # 主角設計圖
│   │   ├── female_character.png
│   │   └── male_character.png
│   ├── storyboards/              # 九宮格與細節圖
│   ├── videos_v2/                # 視頻段（新版）
│   │   ├── 01_Verse1_*.mp4
│   │   ├── 02_PreChorus_*.mp4
│   │   ├── ... (等)
│   │   └── 06_Outro_*.mp4
│   └── final/                    # 最終成品
│       ├── <標題>_完整MV.mp4
│       └── validation_screenshots/
│
├── working/                      # 臨時工作目錄
│   └── <project-id>/
│       ├── concat_list.txt
│       ├── merged_video.mp4
│       └── ...
```

---

## 容易踩的坑

| 坑 | 症狀 | 解決方案 |
|---|------|--------|
| **視頻時長不足** | 合併後 MV 遠短於音樂 | Codex 在生影片時須精確控制時長；使用提示詞中明確指定秒數 |
| **音視頻不同步** | 聲音與畫面明顯錯位 | 檢查 FFmpeg `-shortest` 參數；確認所有視頻段都是 24fps |
| **色彩偏差** | 人物膚色或衣服顏色與設計稿不符 | 確認 FLUX.1 生圖的解析度；在提示詞中加色溫描述（3500K 等） |
| **人物不一致** | 各視頻段的主角臉型 / 衣著不同 | 所有生圖提示詞的開頭都要貼入主角一致性參考詞 |
| **字幕/SRT 錯位** | 字幕時間碼與視頻不對應 | 若使用字幕，必須在步驟 9 後、FFmpeg 組裝時匹配；或在 YouTube 後台手動上傳 SRT |
| **Windows 路徑問題** | 中文檔名或 `[MV]` 括號導致找不到檔 | PowerShell 用單引號或 `-LiteralPath`；Bash 用雙引號 |
| **超出 Groq 限制** | 大檔無法上傳轉錄 | Groq 25MB 上限；使用 Codex 生影片時檔案會自動壓縮 |

---

## 最佳實踐

✅ **做**：
- 每個階段都在 HANDOFF.md 中記錄狀態
- 所有提示詞都用中文撰寫（便於後續調整）
- 生圖 / 生影片前確保提示詞完整
- 驗證時長時用 `ffprobe` 工具檢查
- 保留 `working/` 中的中間產物供稽核

❌ **不做**：
- 不要跳過驗證步驟
- 不要在沒確認時長的情況下開始 FFmpeg 組裝
- 不要拿舊的人物設計圖套新的視頻段
- 不要用 `-y` 自動覆蓋檔案，避免誤覆

---

## 完成檢查清單

完成全流程後，逐項確認：

- [ ] HANDOFF.md 已更新為「完成」狀態
- [ ] outputs/final/ 中有一個完整 MP4 檔
- [ ] VLC 本地播放驗證通過
- [ ] YouTube 非公開連結可正常播放
- [ ] 音視頻同步、色彩正確、解析度 1920×1080
- [ ] 所有中間檔案已整理到對應資料夾
- [ ] 如有字幕，SRT 時間碼已驗證

**全部打勾 ✅ 即可視為本流程完成**

---

## 範例：第一支 MV 的參數紀錄

讓你知道實測 OK 的參數：
- **主題**：「愛情」R&B/Soul，初戀在咖啡廳
- **歌詞**：版權友好版，6 個部分（Verse×2、Chorus、Bridge、Pre-Chorus、Outro）
- **時長**：音樂 216.4 秒 → 視頻 6 段共 216 秒（精確同步）
- **主角**：東亞女性（長直黑髮、米色毛衣）× 東亞男性（短棕髮、焦糖色毛衣）
- **場景**：咖啡廳 + 街道黃昏
- **生影片**：Kling V2.1，1920×1080，成本約 $15
- **最終檔**：outputs/final/愛情_完整MV_2026-05-23.mp4（約 100-200 MB）

---

## 常見提問

**Q: 如果視頻生成失敗怎麼辦？**
A: 檢查提示詞中是否有矛盾之處（例如同時說穿紅衣和黑衣）；簡化提示詞，重新生成；或改用其他生影片模型（Hailuo、Dreamina）。

**Q: 字幕怎麼辦？**
A: 若需要字幕，在 step 7 後使用 `whisper-subtitle` skill 生成 SRT；或在 YouTube 後台自動生成字幕後手動修正。

**Q: 能否邊設計邊生成？**
A: 可以，但建議先完成所有提示詞設計再統一生成，以保持人物一致性和視覺風格。

**Q: Codex 和 Codex 如何分工？**
A: Codex 負責設計與驗證，Codex 負責 AI 生圖生影（media-generation）。FFmpeg 組裝與 YouTube 上傳由 Codex 負責。

---

**準備好開始 MV 製作了嗎？** 🎬✨

每次開工前先讀 HANDOFF.md，每次收工前更新 HANDOFF.md。假設下一個接手者是陌生人！
