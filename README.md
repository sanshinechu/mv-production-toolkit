# 115 Dancing and Music MV

這是一個 AI MV 製作流程指南專案，目前包含 Markdown 指南與靜態網頁介面。

## 使用方式

直接開啟 `index.html` 即可使用，不需要安裝套件，也不需要啟動伺服器。

網頁功能包含：

- MV_01 到 MV_10 步驟導覽
- 每個步驟的目的、輸入、工具、產出
- 可直接複製的 AI 指令
- 常用設定表單，可快速組合 Prompt
- Firebase 匿名登入
- 儲存與讀取自己的 MV 專案設定
- 生成前檢查清單
- 常見修正方向

## Firebase

- Firebase project ID：`dancing-and-music-mv-115`
- Firestore database ID：`mv-projects`
- Firestore 位置：`asia-east1`
- 登入方式：Anonymous Auth
- 資料路徑：`users/{uid}/mvProjects/{projectId}`

Firestore 規則限制每位登入使用者只能讀寫自己的資料。

## 主要檔案

- `index.html`：網頁主畫面
- `styles.css`：網頁樣式
- `script.js`：步驟資料、切換與複製功能
- `firebase-config.js`：前端 Firebase SDK 設定
- `firebase.json`：Firebase 專案設定
- `firestore.rules`：Firestore 安全規則
- `firestore.indexes.json`：Firestore 索引設定
- `MV製作流程指南_10步驟.md`：原始指南
- `MV製作流程指南_第二版.md`：整理後的 SOP 版本

## MV 素材命名建議

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
