# MV 製作 Skills 對應映射

本文檔說明新的 12 步工作流程與現有 Skills 系統的對應關係。

## 概覽

| 新工作流程 | 步驟 | 現有 Skill | 狀態 | 說明 |
|-----------|------|----------|------|------|
| **階段 1：概念到設計** | | | | |
| MV_01 | 歌詞創作與曲風風格 | `mv-01-lyric-songwriting` | ✓ 完全對應 | 無需改動 |
| MV_02 | 主角設計 | `mv-02-character-design` | ✓ 完全對應 | 無需改動 |
| MV_03 | 場景提示詞 | `mv-03-scene-prompt-generation` | ✓ 已對應 | 已新建場景提示詞 skill；舊 `mv-03-image-prompt-generation` 保留為補充（單張影像提示詞）|
| MV_04 | 九宮格分鏡設計 | `mv-04-nine-grid-storyboard` | ✓ 完全對應 | 無需改動 |
| MV_05 | 截圖放大提質 | `mv-05-crop-and-upscale` | ✓ 完全對應 | 無需改動 |
| MV_06 | 影片提示詞設計 | `mv-06-video-prompt-generation` | ✓ 完全對應 | 無需改動 |
| **階段 2：視覺生成** | | | | |
| Step_07 | 圖片和影片生成 | `media-generation` | ✓ 對應 | 通用媒體生成 skill |
| Step_08 | 空拍視角和細節 | `mv-08-drone-shot-generation` | ⚠️ 編號需調整 | 當前編號 mv-08，新流程中也是 Step 8，無需調整邏輯 |
| Step_09 | 電影感打光優化 | `mv-10-cinematic-lighting-reference` | ✓ 已對應 | 用打光參考表即可；skill 編號 mv-10 ≠ 步驟 Step 9，屬歷史編號，非錯誤 |
| Step_10 | FFmpeg 組裝與驗證 | `mv-production-packaging` | ✓ 已涵蓋 | 該 skill 步驟 9️⃣ 已含完整 FFmpeg concat 組裝指令，無需另建 |
| **階段 3：打包上傳** | | | | |
| Step_11 | 打包與資產整理 | `mv-production-packaging` | ⚠️ 部分對應 | 原 skill 涵蓋步驟 10-12，需拆分 |
| Step_12 | YouTube 上傳與發布 | `youtube_publisher` | ✓ 對應 | 現有 skill 完全對應 |

## 詳細對應說明

### ✓ 完全對應（無需改動）

**Step 1: mv-01-lyric-songwriting**
- 功能：根據主題創作適合 SUNO 的歌詞和風格描述
- 新舊對應：完全相同
- 改動：無

**Step 2: mv-02-character-design**
- 功能：設計 MV 主角外觀和氣質（Split Screen 格式）
- 新舊對應：完全相同
- 改動：無

**Step 4: mv-04-nine-grid-storyboard**
- 功能：生成 9 宮格分鏡設計圖
- 新舊對應：完全相同
- 改動：無

**Step 5: mv-05-crop-and-upscale**
- 功能：從九宮格中截取並放大高解析度圖片
- 新舊對應：完全相同
- 改動：無

**Step 6: mv-06-video-prompt-generation**
- 功能：為視頻生成編寫動態效果描述
- 新舊對應：完全相同
- 改動：無

**Step 12: youtube_publisher**
- 功能：自動上傳影片到 YouTube、配置信息
- 新舊對應：完全相同
- 改動：無

---

### ⚠️ 部分對應（需要調整）

**Step 3: mv-03-image-prompt-generation**

**原 Skill 說明**（舊版本）：
- 名稱：「影像生成」
- 功能：生成中文影像提示詞

**新需求**（新版本）：
- 名稱：「場景提示詞」
- 功能：為歌詞段落設計視覺場景（多個場景提示詞）
- 輸出：2-4 個場景提示詞，每個 300-400 字

**建議改動**：
1. Skill 名稱改為 `mv-03-scene-prompt-generation`
2. 說明文中強調「場景設計」而非「影像生成」
3. 明確輸出為「多個場景提示詞」，非「單個影像提示詞」

**原 Skill 功能的去向**：
- 原 MV_03 的「影像提示詞生成」現在融合到 Step 4（九宮格分鏡設計）的提示詞中

---

**Step 8: mv-08-drone-shot-generation**

**編號說明**：
- 舊版本：MV_08（第 8 個模組）
- 新版本：Step 8（第 8 個步驟）
- 結果：編號完全相同，無需改動邏輯

**改動**：
- 無需改動 Skill 本身
- 但在系統中應確保新 Step 8 調用此 Skill

---

**Step 9: mv-10-cinematic-lighting-reference**

**編號說明**：
- 舊版本：MV_10（第 10 個模組）
- 新版本：Step 9（第 9 個步驟）
- 問題：編號不匹配

**改動方案**：
- **選項 A**（推薦）：新建 `mv-09-cinematic-lighting-optimization` Skill
  - 保留原 `mv-10-cinematic-lighting-reference` 作為參考資料 Skill
  - 新 Skill 專門用於 Step 9 的打光優化操作

- **選項 B**（簡單）：改名 `mv-10` 為 `mv-09-cinematic-lighting-reference`
  - 直接改 Skill 編號
  - 風險：可能破壞用戶習慣

**推薦執行選項 A**

---

### ✅ 已解決（原「新增需求」）

**Step 10: FFmpeg 組裝與驗證**

**現狀（已確認）**：
- `mv-production-packaging` 的「步驟 9️⃣ FFmpeg 本地組裝」已包含完整流程：`concat_list.txt` 建立、`ffmpeg -f concat` 串接、音樂合併指令、時長驗證。
- 因此 Step 10 **不需要另建 skill**，直接由 `mv-production-packaging` 涵蓋。

> 註：`mv-production-packaging` 內部用自己的「步驟 9️⃣」標號指稱組裝，對應到 12 步流程的 Step 10——編號不同但功能相符。

---

### ❌ 功能轉移

**mv-07-qversion-illustration（Q 版插圖）**

**現狀**：
- 原 MV_07 步驟中的「圖片處理大師」Skill
- 功能：生成可愛 Q 版插圖

**新工作流程中的角色**：
- 新 Step 7「圖片和影片生成」涵蓋所有圖片生成
- 但 Q 版插圖是可選的補充功能，而非核心流程

**改動方案**：
- 保留 `mv-07-qversion-illustration` Skill（用於補充效果）
- 在新工作流程中標註為「可選擴展」
- 不在 12 步核心流程中，但用戶可在需要時調用

---

**mv-09-google-flow-microfilm（Google Flow 微電影）**

**現狀**：
- 原 MV_09 步驟中的微電影製作 Skill
- 功能：利用首尾幀創造無縫轉場效果

**新工作流程中的角色**：
- 新 Step 6（影片提示詞設計）或 Step 7（生成）可使用此 Skill
- 但不是必須步驟，屬於「可選高級技巧」

**改動方案**：
- 保留 `mv-09-google-flow-microfilm` Skill
- 在 Step 6-7 的「Tips」中提及可選使用此技術
- 不在 12 步核心流程中，但用戶可在需要時調用

---

## 實施建議

### ✅ 已完成

1. **mv-03 場景提示詞** → 已新建 `mv-03-scene-prompt-generation`，Step 3 改指向它；舊 `image-prompt` 保留為補充。
2. **Step 8 調用** → `mv-08-drone-shot-generation` 編號相符，無需改動。
3. **Step 10 FFmpeg** → 確認 `mv-production-packaging` 已涵蓋完整組裝流程，不另建 skill。

### ⏸️ 已評估、決定不做

1. **不新建 `mv-09-cinematic-lighting-optimization`** → Step 9 直接用 `mv-10-cinematic-lighting-reference`（打光參考表）即可，新建反而增加維護負擔。

### 標記可選功能

- **mv-07-qversion-illustration** → 可選擴展（Q 版插圖）
- **mv-09-google-flow-microfilm** → 可選高級技巧（首尾幀微電影）
- **mv-11 / mv-12 / mv-subtitle-scene-sync** → 可選進階自動化工具

---

## 系統級別更新（如需要）

如果用戶界面（例如 system-reminder）中列出了 Skills，需要更新以下映射：

```
- mv-01-lyric-songwriting        → Step 1: 歌詞創作與曲風風格 ✓
- mv-02-character-design         → Step 2: 主角設計 ✓
- mv-03-scene-prompt-generation  → Step 3: 場景提示詞 ✓（image-prompt 為補充）
- mv-04-nine-grid-storyboard     → Step 4: 九宮格分鏡設計 ✓
- mv-05-crop-and-upscale         → Step 5: 截圖放大提質 ✓
- mv-06-video-prompt-generation  → Step 6: 影片提示詞設計 ✓
- media-generation               → Step 7: 圖片和影片生成 ✓
- mv-08-drone-shot-generation    → Step 8: 空拍視角和細節 ✓
- mv-10-cinematic-lighting-reference → Step 9: 電影感打光優化 ✓（用參考表）
- mv-production-packaging        → Step 10-12: 組裝、打包、發布 ✓
- youtube-publisher              → Step 12: YouTube 上傳與發布 ✓
（可選進階：mv-11-timeline-storyboard、mv-12-shots-generator、mv-subtitle-scene-sync）
```

---

## 後續新增的 Skills（本映射初版之後才加入）

這幾個 skill 在 2026-05-25 初版映射之後才建立，屬於「進階／自動化」工具，可穿插在 12 步流程中使用：

| Skill | 定位 | 在 12 步中的位置 |
|-------|------|------------------|
| `mv-11-timeline-storyboard` | 分析歌曲音訊（word-level 歌詞時間戳 + 音量能量曲線），產出切點對齊音樂的變動秒數分鏡表 | Step 3~4 的進階版：用實際音訊驅動分鏡時間軸 |
| `mv-12-shots-generator` | 讀分鏡表/prompts 清單，用免費生圖管道（Cloudflare Workers AI 優先、Pollinations 備援）批次產圖 | Step 7 的自動化：照分鏡批次生圖 |
| `mv-subtitle-scene-sync` | 依歌詞節奏與音樂長度，精算 FFmpeg 變速參數與 SRT 時間碼，讓場景切換／字幕／音樂同步 | Step 10 的輔助：組裝時的字幕與變速對齊 |

> 這三個是「可選進階工具」，不佔 12 步核心格子，但實際製作時很常用。

---

## 目前 skill 總覽

`.claude/skills/` 目前共 **18 個** skill（含上表三個新增與 `MV_WORKFLOW_GUIDE` 導航、`media-generation` 通用生成、`mv-07-qversion-illustration` 可選 Q 版、`mv-09-google-flow-microfilm` 可選微電影）。skill 的 `mv-XX` 編號沿用舊的 10 模組時代，**與 12 步流程的 Step 編號不是一一對應**，對照請以本文件為準。

---

## 變更日誌

- **2026-07-06**：對齊現況（v2.1）
  - 修正 Step 3 對應到 `mv-03-scene-prompt-generation`（已新建）
  - Step 9、Step 10 標為已對應：打光用參考表、組裝由 `mv-production-packaging` 涵蓋
  - 補入 `mv-11`、`mv-12`、`mv-subtitle-scene-sync` 三個後續新增 skill
  - 補充「目前共 18 個 skill」與編號說明
  - 修好 `mv-03-scene-prompt-generation`、`mv-production-packaging` 兩個 skill 壞掉的 `name:` 欄位

- **2026-05-25**：初始映射（v2.0）
  - 從 10 個 MV 模組改為 12 步工作流程
  - 大部分 Skills 保持對應
  - 部分 Skills 編號需調整

