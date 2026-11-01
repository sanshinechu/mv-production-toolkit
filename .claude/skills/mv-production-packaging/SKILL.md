---
name: MV 交件收尾
description: MV 影片素材都生好之後的收尾：收片檢查（collect_videos）、組裝（make_mv）、自動檢查（review_mv）、三家抽幀停損點、打包與 YouTube 上傳。使用者說「組裝 MV」「MV 交件」「打包上傳 MV」或「使用 mv-production-packaging」時使用。要從頭做一支 MV（企劃到生影片）看 MV_WORKFLOW_GUIDE 與 docs/影片分流策略.md，不是這支。適用於 Claude Code、Codex 與其他已授權 AI。
---

# MV 交件收尾：組裝、檢查、抽幀、打包、上傳

> 📏 **先讀《影片製作 6 項基本原則》**：`docs/影片製作基本原則.md`（01_MV製作 專案內，唯一正本）。交件前一定要實際抽幀，未抽幀不得宣稱通過。

> 🛑 **上傳授權（硬性）**：YouTube 上傳（含排程、改公開）前，先把檔案、標題、隱私設定列給使用者，**取得當次明確同意才執行**；之前同意過的不算數。一律先 `private`。

> 📌 2026-11-01 改成短版：本 skill 只負責**影片素材都生好之後**的收尾。前面的步驟（企劃、分鏡、影片提示詞、四條影片路線）看 `MV_WORKFLOW_GUIDE` 與 `docs/影片分流策略.md`。
> 舊版 11 步（HANDOFF.md、media-generation 生影片、FFmpeg `concat`、VLC 驗證）已搬到 `docs/_歷史/mv-production-packaging_舊版/`，**不要照做**。

## 前提

- 專案是用 `python scripts/new_mv.py "<MV名>"` 建的 `outputs/<MV名>/`。
- 分鏡表是 `outputs/<MV名>/storyboard_vN.md`（mv-11 產出，**三支腳本共用這一份，不要各自改秒數**）。
- 影片已照分流策略生好，放在 `outputs/<MV名>/videos-raw/cutNN_<短名>.mp4`（🅰 用 `collect_videos.py` 從 `colab_mv/outputs/` 搬回）。

## 步驟

1. **收片檢查**
   ```
   python scripts/collect_videos.py <MV名> --storyboard outputs/<MV名>/storyboard_vN.md --check
   ```
   擋缺鏡、秒數不足、不是 1920×1080、不是 24 fps、檔名對不上分鏡表。沒過就回該鏡補生，不要硬組。
2. **組裝**
   ```
   python scripts/make_mv.py --videos outputs/<MV名>/videos-raw --storyboard outputs/<MV名>/storyboard_vN.md --size 1920x1080 --music <歌.mp3> --out outputs/<MV名>/<MV名>_完整MV.mp4
   ```
   會裁到分鏡秒數、丟原聲、做兩段式響度；唱歌鏡讀 `videos-raw/_sing_cuts.json` 不加速；低解析度或非 24 fps 會直接停（真的要硬用才加 `--allow-lowres`／`--allow-fps`，並在交件紀錄寫明）。有口白／音效的微電影另加 `--audio-cues`（見 mv-14）。
3. **自動檢查**
   ```
   python scripts/review_mv.py outputs/<MV名>/<MV名>_完整MV.mp4 --music <歌.mp3> --storyboard outputs/<MV名>/storyboard_vN.md
   ```
   產出 `review/` 的 `<片名>_pass1.jpg`（逐鏡抽格）與 `<片名>_cuts.jpg`（切點前後並排）。
4. ⛔ **抽幀停損點（三家都看過才算完成）**：`review_mv.py` 全綠**不等於**可以交件。Claude／Codex／Antigravity 各自**親眼打開**那兩張圖，逐張確認：字幕帶淨空、沒有亂碼字或浮水印、角色沒崩（臉、手、人數、服裝）、轉場落點對。**三家都說 OK 才算過**，任何一家指出問題就處理（判斷不一致用像素差異圖之類的量測定案）。有問題 → 回該鏡重生 → 重新 collect → 組裝 → 再看。通過後在每日筆記記「抽幀三家已看、日期、各家結論」。
5. **打包**：`outputs/<MV名>/` 照 `MV專案範本/` 的結構；`metadata.md` 寫 YouTube 描述／章節／標籤（可參考同資料夾的 `metadata-template.md`）；封面 `cover.png` 1920×1080。
6. **上傳**：用共用上傳腳本，指令與注意事項見專案 `CLAUDE.md`「上傳 YouTube（仍有效）」——先 `--dry-run`；MV 要加 `--title` 與 `--category 10`；先 `private`，老師說公開才改。跑完把 `youtube-upload.json` 的連結記進每日筆記。
7. **封存**：上架後老師會把資料夾移出 `outputs/`，放到各台自己的封存位置；之後在 `outputs/` 找不到不代表遺失，先問老師。
