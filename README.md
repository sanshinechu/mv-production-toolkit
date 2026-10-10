# 01_MV製作（mv-production-toolkit）

AI MV 製作工具箱：12 支 MV skill 的專案副本、三方共審接點、Colab H3／Google Flow 影片分流、組裝與檢查腳本。

## 現行流程（2026-10）

```
新專案       python scripts/new_mv.py "<MV名>"  → outputs/<MV名>/（照裡面 README 的進度檢核做）
企劃～影片提示詞  15_ai共筆工作流 cowrite --flow mv（影片提示詞為審核模式，三家「無意見」）
分鏡表       mv-11 → outputs/<MV名>/storyboard_vN.md（所有腳本共用）
影片分流 🅰  Colab H3：--flow mv-h3 審核 → h3_specs_from_review.py → h3_batch.py（Claude 經 colab_bridge.py 代跑）
         🅱  Google Flow：--flow mv-flow 審核 → 老師在 Flow 生成
收片檢查     collect_videos.py（1920×1080、24 fps、秒數、缺鏡）
組裝         make_mv.py --videos --storyboard --size 1920x1080 → review_mv.py
⛔ 人工抽幀  老師看 review/ 兩張圖說 OK 才算完成 → 打包上傳
```

- **影片路線唯一依據**：[docs/影片分流策略.md](docs/影片分流策略.md)（其他文件只連過去，不抄）
- 畫面規範：[docs/影片製作基本原則.md](docs/影片製作基本原則.md)
- 單一 MV 範本：[MV專案範本/](MV專案範本/)
- MV skill 正本在 dotfiles `.skills/`，同步方式見 [CLAUDE.md](CLAUDE.md)「MV skill 的正本與同步」
- 舊流程（10 步、第二版、舊專案範本、九宮格大圖、Wan 本機）都在 [docs/_歷史/](docs/_歷史/)，**不要照著做**

---

## 網頁介面（舊版 12 步導覽，仍可用）

這是一個 AI MV 製作流程指南專案，目前包含 Markdown 指南與靜態網頁介面。

## 使用方式

直接開啟 `index.html` 即可使用，不需要安裝套件，也不需要啟動伺服器。

網頁功能包含：

- MV 製作 12 步（Step 1 到 Step 12）步驟導覽
- 每個步驟的目的、輸入、工具、產出
- 可直接複製的 AI 指令
- 常用設定表單，可快速組合 Prompt
- Firebase Google 登入
- 儲存與讀取自己的 MV 專案設定
- 生成前檢查清單
- 常見修正方向

## Firebase

- Firebase project ID：`dancing-and-music-mv-115`
- 資料庫：**Realtime Database**（網頁實際使用；規則見 `database.rules.json`）
- 登入方式：Google 登入
- 資料路徑：`users/{uid}/mvProjects/{projectId}`

安全規則限制每位登入使用者只能讀寫自己的資料。

> 註：專案也設定了 Firestore（`firestore.rules`、`firestore.indexes.json`、ID `mv-projects`、位置 `asia-east1`），但目前前端網頁未使用，保留作為日後擴充的備用。

## 主要檔案

- `index.html`：網頁主畫面
- `styles.css`：網頁樣式
- `script.js`：步驟資料、切換與複製功能
- `firebase-config.js`：前端 Firebase SDK 設定
- `firebase.json`：Firebase 專案設定
- `database.rules.json`：Realtime Database 安全規則（網頁實際使用）
- `firestore.rules`：Firestore 安全規則（備用，前端未使用）
- `firestore.indexes.json`：Firestore 索引設定（備用）
- 舊版指南已移到 `docs/_歷史/`

## MV 素材命名建議（舊網頁版；新專案改用 `MV專案範本/` 的結構）

- `01_歌詞與曲風.md`
- `02_主角設計_prompt.md`
- `03_主角參考圖.png`
- `04_九宮格分鏡.png`
- `05_分鏡放大_01.png`
- `06_影片提示詞_01.md`
- `07_角色風格變體_01.png`
- `08_空拍圖_01.png`
- `09_Flow_首尾幀提示詞_01.md`
- `10_電影感打光指令_01.md`
- `output_Flow_成品片段_01.mp4`

## 建議下一步

- 補一組「從主題到成品」的完整示範
- 依實際使用情境微調各步驟 Prompt
- 若要對外分享，再視需求啟用 GitHub Pages
