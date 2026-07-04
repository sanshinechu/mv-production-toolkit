# MV 製作完整工作流 - Skill 簡明指南

## 🎬 這個 Skill 是什麼？

這是 MV 製作專案的**總控技能**，整合了從歌詞創作、角色設計、視覺設計、到影片生成、組裝、上傳的**完整 11 步驟工作流**。

適用於 **Claude Code 和 Codex 的雙 AI 協作模式**。

---

## ⚡ 快速開始

### 場景 1：完全從零開始製作新 MV

```
使用者：「我想製作一個 R&B/Soul 風格的愛情 MV，主角是初戀情侶，場景在咖啡廳」

→ Claude Code 開始 MV_01（歌詞創作）
→ 使用者上傳 SUNO 音樂到 outputs/
→ Claude Code 執行 MV_02-07（設計所有提示詞）
→ 更新 HANDOFF.md，交接給 Codex
→ Codex 執行 media-generation（生圖 + 生影片）
→ Claude Code 執行 FFmpeg 組裝、VLC 驗證、YouTube 上傳
→ 完成！🎉
```

### 場景 2：已有歌詞與音樂，從設計開始

```
使用者：「音樂已經生好了，我的 SUNO 檔案在 outputs/music.mp3」

→ Claude Code 跳過 MV_01，從 MV_02 開始（主角設計）
→ ... (同上) ...
```

### 場景 3：發現視頻時長不足，需要重新生成

```
使用者：「音樂 216 秒但視頻只有 24 秒，需要重新生成」

→ Claude Code 更新 HANDOFF.md 記錄問題
→ Claude Code 為每個歌詞部分生成新的「完整長度」視頻提示詞
→ 交接 Codex 重新生成視頻段（Verse 30s、Chorus 30s 等）
→ 回到 FFmpeg 組裝 ...
```

---

## 📋 核心流程（簡版）

| # | 步驟 | 工作 | 負責 | 時間 |
|---|------|------|------|------|
| 1 | 歌詞 | MV_01：創作歌詞 + SUNO 風格 | Claude | 30-45 分 |
| 2 | 音樂 | SUNO：生成 MP3 | 使用者 | 30-60 分 |
| 3 | 角色 | MV_02：設計主角（女+男） | Claude | 15-30 分 |
| 4-7 | 設計 | MV_03-06：所有視覺提示詞 | Claude | 120-160 分 |
| 8 | 生成 | media-generation：圖片+視頻 | Codex | 60-120 分 |
| 9 | 組裝 | FFmpeg：合併視頻段+音樂 | Claude | 10-15 分 |
| 10 | 驗證 | VLC：本地播放檢查 | Claude | 10-15 分 |
| 11 | 上傳 | **youtube_publisher**：快速發布 | Claude | **15-30 分** |
| 12 | 打包 | 整理成品與 metadata | Claude | **5-10 分** |

---

## 🔴 最重要的檔案

### HANDOFF.md

**這是項目的生命線**

- 所有交接信息都在這裡
- 每次工作前先讀「目前狀態」區段
- 每次工作後更新「下一步」與進度

```
HANDOFF.md 應包含：
✅ 當前狀態（哪個步驟正在進行）
✅ 已完成的提示詞與資源
✅ 待執行的任務
✅ 交接給下一個 AI 的明確指示
```

### 三個追蹤文件

```
<雲端硬碟根目錄>\claude and codex\MV製作\
│
├── HANDOFF.md                      ← 中央交接（最重要）
├── MV製作進度追蹤.md              ← Obsidian 進度表
└── 工作筆記本/每日筆記/2026-05-23.md ← 工作日誌
```

---

## 🚨 常見問題

### Q: 視頻生成時，時長怎麼控制？

**A:** 在提示詞中明確指定秒數

❌ **錯誤**：
```
「兩人牽手漫步，光線溫暖」← 沒說多長
```

✅ **正確**：
```
「兩人牽手漫步 30 秒，慢速追蹤運鏡...」
```

### Q: 為什麼強調「主角一致性參考詞」？

**A:** Codex 每次生圖時都必須看到相同的角色描述，否則人物會長得不一樣

所以每個視頻提示詞的開頭都要有：
```
[FEMALE_CHARACTER] East Asian woman, long straight black hair, cream sweater, ...
[MALE_CHARACTER] East Asian man, short brown hair, caramel sweater, ...
```

### Q: 如果 Codex 生不出來怎麼辦？

**A:** 在 HANDOFF.md 中記錄失敗的提示詞，簡化它，重新生成

範例：
```
#### ❌ 失敗提示詞（太複雜）
Verse 1 - 初戀悸動（30 秒）
女主角坐在咖啡廳靠窗座位，
窗外有樹，陽光透過樹葉灑進來，
背景有其他顧客在模糊的環境中...

#### ✅ 簡化後（刪掉干擾元素）
Verse 1 - 初戀悸動（30 秒）
女主角坐在咖啡廳靠窗座位，
陽光透過窗戶照在她臉上，
溫暖而柔和的光線...
```

### Q: FFmpeg 組裝失敗怎麼辦？

**A:** 檢查：

1. 視頻檔都存在嗎？
   ```bash
   ls -lh outputs/videos_v2/*.mp4
   ```

2. 音樂檔存在嗎？
   ```bash
   ls -lh outputs/*.mp3
   ```

3. concat_list.txt 的路徑對嗎？
   ```
   file '01_Verse1_初戀悸動.mp4'  ← 檔名要完全相同
   ```

4. FFmpeg 語法正確嗎？
   ```bash
   ffmpeg -f concat -safe 0 -i concat_list.txt \
     -c:v libx264 -c:a aac merged_video.mp4
   ```

---

## 📂 檔案結構

```
.claude/skills/mv-production-packaging/
│
├── SKILL.md                    ← 完整流程說明（這個 Skill 本身）
└── README.md                   ← 快速指南（你正在讀這個）
```

---

## 📤 Step 11-12：YouTube 上傳與打包

### Step 11：YouTube 上傳（使用 youtube_publisher）

第 11 步使用 **youtube_publisher skill** 進行快速上傳，取代傳統的人工 YouTube Studio 操作。

**為什麼使用 youtube_publisher？**

| 優勢 | 傳統上傳 | youtube_publisher |
|-----|--------|------------------|
| **速度** | 5-10 分 + 等待 15-30 分 = 20-40 分 | 15-30 分（整合所有步驟） |
| **精確度** | 手動填入，易出錯 | 自動從 HANDOFF.md 提取 |
| **可重複性** | 每次都要手動 | 相同參數可批量上傳 |
| **驗證** | 需手動檢查 | 內建自動驗證報告 |
| **整合** | 無縫接 | 直接與工作流同步 |

**上傳流程**：
```
Step 10: VLC 本地驗證完成 ✅
         ↓
Step 11: youtube_publisher 上傳
         - 輸入：outputs/final/<標題>_完整MV.mp4
         - 元數據：從 HANDOFF.md 複製（標題、描述、標籤）
         ↓
YouTube 處理完成 ✅
         ↓
Step 12: 打包與資產整理
```

**檢查清單（上傳後）**：
- [ ] 影片已完成上傳和處理（不再顯示「處理中」）
- [ ] 解析度正確（1920×1080）
- [ ] 音視頻同步（無延遲）
- [ ] 元數據正確顯示
- [ ] 複製最終 YouTube 連結

---

### Step 12：打包與資產整理（新增）

第 12 步（參考剪片工作流）將所有成品整理到專業結構的資料夾，並生成完整的 metadata。

**最終輸出結構**：

```
outputs/<MV標題> [Claude]/
├── <MV標題>_完整MV.mp4          ← 最終影片
├── cover.png                     ← YouTube 封面
├── metadata.md                   ← 完整元數據（7 區塊）
├── README.md                     ← 製作簡介
└── source-assets/               ← 源素材備份（可選）
    ├── characters/
    ├── storyboards/
    └── videos_v2/
```

**metadata.md 的 7 區塊結構**：

1. **YouTube 描述** — 開場 2-3 句 + 重點列表
2. **章節時間碼** — 按歌曲結構標記時間點
3. **社群版本** — Facebook / Instagram / Threads 分別撰寫
4. **SEO 關鍵字** — 主 / 次 / 長尾 / 競品分組
5. **YouTube 標籤** — 「全部一次貼」直接複製版本
6. **上架前 Checklist** — 最後驗證清單
7. **額外資訊** — 製作工具、製作時間等

**檢查清單（打包後）**：

- [ ] 資料夾名稱：`outputs/<MV標題> [Claude]/`
- [ ] 核心三檔案齊全：MP4 + cover.png + metadata.md
- [ ] MP4 解析度 1920×1080、音視頻同步
- [ ] metadata.md 含 7 區塊、無排版錯誤
- [ ] YouTube 連結已記錄到 HANDOFF.md
- [ ] 社群貼文已排期發佈

---

## 🎨 資產管理與風格指南（推薦）

參考剪片工作流的最佳實踐，建立以下資料夾結構：

```
MV製作/
├── assets/
│   ├── persona/                    ← 主角人物形象參考
│   │   ├── README.md              ← 主角介紹
│   │   ├── female_character.png   ← 女主角參考照
│   │   └── male_character.png     ← 男主角參考照
│   │
│   └── style/                      ← 視覺風格指南
│       ├── README.md              ← 風格指南說明
│       ├── cover-style.md         ← YouTube 封面風格
│       ├── color-palette.md       ← 色彩設定
│       └── reference-thumbnails/  ← 參考封面範例
│
└── outputs/
    └── <MV標題> [Claude]/
        ├── <MV標題>_完整MV.mp4
        ├── cover.png
        ├── metadata.md
        └── ...
```

### 主角人物檔案（assets/persona/）

建立 README.md 說明主角背景：

```markdown
# 主角人物介紹

## 女主角

- **角色名**：（可選）
- **年齡背景**：學生、初戀
- **視覺特徵**：長直黑髮、米色毛衣、溫柔甜蜜
- **性格特質**：害羞、期待、溫柔
- **一致性參考詞**（複製到所有生圖提示詞）：
  ```
  [FEMALE_CHARACTER] East Asian woman, long straight black hair, cream sweater, gentle and sweet expression
  ```

## 男主角

- **角色名**：（可選）
- **年齡背景**：學生、初戀
- **視覺特徵**：短棕髮、焦糖色毛衣、溫暖體貼
- **性格特質**：溫柔、專注、深情
- **一致性參考詞**（複製到所有生圖提示詞）：
  ```
  [MALE_CHARACTER] East Asian man, short brown hair, caramel sweater, warm and caring expression
  ```
```

### 風格指南（assets/style/）

建立 README.md 說明整體視覺方向：

```markdown
# 視覺風格指南

## 色彩主調

- **主色調**：暖色系（金色、棕色、米色）
- **輔色**：天藍色、淡粉紅
- **背景色**：柔和米白或淡灰

## 光影風格

- **整體風格**：溫暖、甜蜜、電影感
- **推薦打光**：黃金時刻光線（Golden Hour）、體積光
- **色溫**：3500-4500K（暖白光）

## 場景風格

- **主要場景**：咖啡廳（室內溫馨感）
- **視覺調性**：文藝、溫暖、有故事感
- **構圖風格**：電影橫幅（16:9）、淺景深突出主角

## 參考資源

- 參考電影：《你的名字》、《言葉之庭》等日系青春愛情電影風格
- 參考 MV：[列出 3-5 個風格相近的參考 MV]
```

---

## 💡 設計理念

這個 Skill 的設計靈感來自 **剪片工作流** 的 `claude-youtube-video-workflow`，有相似的特點：

✅ **明確的交接點**：每個步驟都知道誰負責、期望何時完成  
✅ **單一真實來源**：HANDOFF.md 是唯一的中央檔案  
✅ **可重現的流程**：同一個 Skill 再跑一遍能產出相同品質  
✅ **踩坑紀錄**：將常見問題與解決方案寫進文檔  
✅ **最後一步簡化**：使用 youtube_publisher 讓上傳環節自動化和標準化

---

## 🎯 下一步

當你開始新的 MV 製作時：

1. **讀一遍 SKILL.md**（約 15 分鐘）
2. **檢查 HANDOFF.md 的「目前狀態」**
3. **根據進度選擇從哪個步驟開始**
4. **每做完一個步驟就更新 HANDOFF.md**
5. **第 11 步使用 youtube_publisher 快速上傳**

---

**準備好用 mv-production-packaging 製作你的第一個 MV 了嗎？** 🎬✨
