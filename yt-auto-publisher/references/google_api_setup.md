# YouTube Data API v3 — Google Cloud Console 設定教學

作者：阿亮老師・3A科技研究社

本文件提供完整的圖文步驟，引導您從零開始設定 YouTube Data API v3 的 OAuth2 憑證。

---

## 前置需求

- 一個 Google 帳號（Gmail）
- 該帳號已建立 YouTube 頻道
- 瀏覽器（Chrome 建議）

---

## 步驟 1：前往 Google Cloud Console

1. 開啟瀏覽器，前往 **[Google Cloud Console](https://console.cloud.google.com/)**
2. 使用您的 Google 帳號登入
3. 如果是第一次使用，需要同意服務條款

> 畫面截圖位置：Google Cloud Console 首頁儀表板
> https://console.cloud.google.com/
> 您會看到頂部導覽列、左側選單、中間是專案概覽

---

## 步驟 2：建立新專案

1. 點擊頂部導覽列的 **專案選擇器**（通常顯示「Select a project」或已有專案名稱）
2. 在彈出視窗中點擊 **「新增專案」(NEW PROJECT)**
3. 填寫專案資訊：
   - **專案名稱**：輸入辨識名稱，例如 `YouTube-Uploader`
   - **機構**：若無特殊需求保留預設
   - **位置**：保留預設
4. 點擊 **「建立」(CREATE)**
5. 等待專案建立完成（約 10-30 秒）
6. 確認頂部導覽列已切換到新專案

> 直達連結：https://console.cloud.google.com/projectcreate
>
> 畫面說明：專案建立頁面，上方有「專案名稱」輸入框，
> 下方有「機構」和「位置」欄位，右下角有「建立」按鈕

---

## 步驟 3：啟用 YouTube Data API v3

1. 在左側選單點擊 **「API 和服務」>「程式庫」**
   或直接前往：https://console.cloud.google.com/apis/library
2. 在搜尋框輸入 `YouTube Data API v3`
3. 點擊搜尋結果中的 **「YouTube Data API v3」**
4. 點擊 **「啟用」(ENABLE)** 按鈕
5. 等待啟用完成

> 直達連結：https://console.cloud.google.com/apis/library/youtube.googleapis.com
>
> 畫面說明：API 詳細頁面，顯示 YouTube Data API v3 的說明，
> 右上方或中間有藍色的「啟用」按鈕。啟用後按鈕會變成「管理」

---

## 步驟 4：設定 OAuth 同意畫面

在建立 OAuth 憑證之前，必須先設定同意畫面。

1. 前往 **「API 和服務」>「OAuth 同意畫面」**
   或直接前往：https://console.cloud.google.com/apis/credentials/consent
2. **選擇 User Type**：
   - 選擇 **「外部」(External)**（除非您有 Google Workspace 組織帳號）
   - 點擊 **「建立」(CREATE)**

> 畫面說明：選擇使用者類型頁面，有「內部」和「外部」兩個選項，
> 外部選項下方說明「任何擁有 Google 帳戶的使用者」

3. **填寫應用程式資訊**：
   - **應用程式名稱**：`YouTube Uploader`（或您喜歡的名稱）
   - **使用者支援電子郵件**：選擇您的 Gmail
   - **應用程式標誌**：（可跳過）
   - **應用程式首頁**：（可跳過）
   - **開發人員聯絡資訊**：填入您的 Email
   - 點擊 **「儲存並繼續」**

4. **設定範圍 (Scopes)**：
   - 點擊 **「新增或移除範圍」**
   - 在篩選器中搜尋以下範圍並勾選：
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
     - `https://www.googleapis.com/auth/youtube.readonly`
   - 或直接在「手動新增範圍」輸入以上網址
   - 點擊 **「更新」**
   - 點擊 **「儲存並繼續」**

> 畫面說明：範圍設定頁面，左側有搜尋和過濾選項，
> 右側是範圍清單與勾選框。底部有「更新」按鈕

5. **新增測試使用者**：
   - 點擊 **「+ ADD USERS」**
   - 輸入您自己的 Gmail 信箱
   - 點擊 **「新增」**
   - 點擊 **「儲存並繼續」**

> 重要：在應用程式尚未通過 Google 審核之前，只有測試使用者能夠授權。
> 請務必將您自己的 Gmail 加入測試使用者。

6. 檢閱摘要，點擊 **「返回資訊主頁」**

---

## 步驟 5：建立 OAuth2 客戶端 ID

1. 前往 **「API 和服務」>「憑證」**
   或直接前往：https://console.cloud.google.com/apis/credentials
2. 點擊頂部的 **「+ 建立憑證」(+ CREATE CREDENTIALS)**
3. 選擇 **「OAuth 用戶端 ID」(OAuth client ID)**
4. 填寫設定：
   - **應用程式類型**：選擇 **「電腦版應用程式」(Desktop app)**
   - **名稱**：`YouTube Uploader Desktop`（或自訂名稱）
5. 點擊 **「建立」(CREATE)**

> 直達連結：https://console.cloud.google.com/apis/credentials/oauthclient
>
> 畫面說明：建立 OAuth 用戶端 ID 頁面，有「應用程式類型」下拉選單
> 和「名稱」輸入框

6. **建立完成後**，會彈出一個視窗顯示：
   - 用戶端 ID
   - 用戶端密鑰
   - **「下載 JSON」** 按鈕

7. 點擊 **「下載 JSON」** 按鈕，儲存檔案

> 畫面說明：「OAuth 用戶端已建立」對話框，顯示用戶端 ID 和密鑰，
> 底部有「確定」和「下載 JSON」按鈕

---

## 步驟 6：放置憑證檔案

1. 將下載的 JSON 檔案重新命名為 `client_secrets.json`
2. 複製到以下路徑：

```
C:\Users\user\.claude\skills\yt-auto-publisher\credentials\client_secrets.json
```

您可以使用命令列：

```bash
# 建立目錄
mkdir -p "C:/Users/user/.claude/skills/yt-auto-publisher/credentials"

# 複製檔案（請替換實際下載路徑）
cp ~/Downloads/client_secret_*.json \
   "C:/Users/user/.claude/skills/yt-auto-publisher/credentials/client_secrets.json"
```

---

## 步驟 7：首次 OAuth2 授權

1. 執行授權腳本：

```bash
cd "C:/Users/user/.claude/skills/yt-auto-publisher"
python scripts/setup_credentials.py --auth
```

2. 瀏覽器會自動開啟 Google 登入頁面
3. 選擇您的 Google 帳號
4. 您可能會看到 **「Google 尚未驗證這個應用程式」** 的警告：
   - 點擊 **「進階」(Advanced)**
   - 點擊 **「前往 YouTube Uploader（不安全）」**

> 畫面說明：Google 安全警告頁面，因為應用程式尚未通過審核。
> 這是正常的，因為這是您自己的應用程式。

5. 在授權頁面勾選所有權限，點擊 **「繼續」(Continue)**
6. 看到 **「授權成功！您可以關閉此頁面。」** 即完成

7. 回到終端機，應該會看到：
   - `授權成功！權杖已儲存至 .../credentials/token.json`
   - `已連接頻道：[您的頻道名稱]`

---

## 驗證設定

執行以下指令確認一切就緒：

```bash
python scripts/setup_credentials.py --check
```

應該顯示：
```
  Python 套件：已安裝
  client_secrets.json：已存在
    格式正確（OAuth2 客戶端憑證）
  token.json：已存在
    權杖有效
```

---

## 常見問題

### Q: 看到「Access blocked: This app's request is invalid」

**原因**：OAuth 同意畫面未正確設定。
**解法**：
1. 回到步驟 4，確認已設定 OAuth 同意畫面
2. 確認應用程式類型是「外部」
3. 確認已新增測試使用者

### Q: 看到「Error 403: access_denied」

**原因**：您的 Gmail 不在測試使用者清單中。
**解法**：
1. 前往 OAuth 同意畫面 > 測試使用者
2. 新增您的 Gmail 信箱

### Q: 上傳時出現配額錯誤

**原因**：YouTube Data API v3 有每日配額限制（預設 10,000 單位，一次上傳耗費 1,600 單位）。
**解法**：
1. 每天約可上傳 6 支影片
2. 如需更多配額，前往 Google Cloud Console > API 和服務 > YouTube Data API v3 > 配額
3. 點擊「編輯配額」申請增加

### Q: token.json 過期怎麼辦？

**解法**：腳本會自動重新整理權杖。如果自動重新整理失敗：
1. 刪除 `credentials/token.json`
2. 重新執行 `python scripts/setup_credentials.py --auth`

### Q: 想在其他電腦使用

**做法**：
1. 複製 `credentials/client_secrets.json` 到新電腦
2. 在新電腦執行 `python scripts/setup_credentials.py --auth` 重新授權
3. `token.json` 不可跨電腦使用，每台電腦需個別授權

---

## 安全注意事項

- **`client_secrets.json`** 和 **`token.json`** 包含敏感資訊
- 請勿將這些檔案上傳到 GitHub 或其他公開空間
- 建議在 `.gitignore` 中加入 `credentials/`
- 如果懷疑憑證外洩，請立即到 Google Cloud Console 撤銷並重新建立

---

## API 配額參考

| 操作 | 配額消耗（單位） |
|------|------------------|
| 上傳影片 | 1,600 |
| 列出影片 | 1 |
| 更新影片中繼資料 | 50 |
| 列出播放清單 | 1 |
| 建立播放清單 | 50 |
| 新增播放清單項目 | 50 |
| 設定縮圖 | 50 |

預設每日配額：10,000 單位
相當於每天約上傳 6 支影片（含中繼資料操作）

---

文件更新日期：2026-04-11
作者：阿亮老師・3A科技研究社
