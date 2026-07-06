# Firebase 保存功能修復指南

## 問題診斷

你的保存功能無法運作，原因是 **Realtime Database 的 Security Rules 未正確設置**。

### 目前的配置狀況

✓ 應用程式代碼：正確（Firebase 初始化、Google 認證、保存邏輯都沒問題）
✓ Firebase 配置：正確（firebaseConfig 與 Firebase 項目匹配）
✓ Google 認證：正確（按鈕能夠登入）
❌ **Security Rules**：錯誤（只有 Firestore 規則，沒有 Realtime Database 規則）

### 為什麼會這樣

- 你有 `firestore.rules`（Cloud Firestore 的規則）
- 但你的程式碼使用 **Realtime Database**（不同的服務）
- Realtime Database 沒有對應的安全規則，導致寫入被拒絕或失敗

---

## 快速修復（3 步驟）

### 步驟 1：打開 Firebase 控制台

訪問：https://console.firebase.google.com/

選擇項目：**dancing-and-music-mv-115**

### 步驟 2：進入 Realtime Database

1. 左側菜單 → **Realtime Database**
2. 找到你的數據庫（應該在 asia-southeast1 區域）
3. 點擊「Rules」標籤

### 步驟 3：複製並貼上新規則

將下面的規則**完全替換**現有的內容：

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "auth.uid === $uid",
        ".write": "auth.uid === $uid",
        "mvProjects": {
          ".read": "auth.uid === $uid",
          ".write": "auth.uid === $uid"
        }
      }
    }
  }
}
```

### 步驟 4：發布規則

點擊「發布」按鈕，等待部署完成（通常 5-10 秒）。

你會看到綠色的「Published」確認訊息。

---

## 驗證修復是否成功

修復後，試試以下操作：

1. 打開網站，點擊「使用 Google 登入」
2. 用你的 Google 帳號登入
3. 填入「專案名稱」和其他信息
4. 點擊「儲存專案」按鈕
5. 看到綠色的「✓ 專案已保存！」訊息

然後回到 Firebase 控制台：
- **Realtime Database** → 點擊「Data」標籤
- 應該能看到你的用戶 ID 和保存的專案資料

---

## 規則說明

新規則的意思：
- `users/{uid}` 下的數據只能被該用戶本人讀寫
- `mvProjects` 也是只有該用戶能訪問
- 其他用戶無法看到或修改你的數據

---

## 如果還是不行

按照瀏覽器控制台（F12）的錯誤訊息：

1. 打開網站 → 按 **F12**
2. 點擊「Console」標籤
3. 點擊「儲存專案」按鈕
4. 查看紅色的錯誤訊息
5. 告訴我具體的錯誤代碼（通常是 `permission-denied` 或 `auth/...` 開頭）

---

## 備註

- 如果你有 Firebase CLI 裝在電腦上，可以執行 `firebase deploy --only database` 來自動部署規則
- 不過手動在 Firebase 控制台設置也很簡單，只需 5 分鐘
