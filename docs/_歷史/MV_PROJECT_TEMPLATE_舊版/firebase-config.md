# Firebase 配置指南

本專案支援 Firebase 用於儲存 MV 專案進度和元數據。本指南說明如何設置 Firebase。

## 為什麼使用 Firebase？

- 🔐 安全儲存專案數據
- 📊 追蹤多個 MV 專案的進度
- 👥 支持團隊協作（如需要）
- ☁️ 雲端備份，防止數據丟失

## 設置步驟

### 1. 創建 Firebase 專案

1. 訪問 [Firebase Console](https://console.firebase.google.com/)
2. 點擊「建立專案」
3. 輸入專案名稱（例：`mv-production`）
4. 選擇計費方案（Spark Plan 免費）
5. 按照提示完成設置

### 2. 啟用 Realtime Database

1. 在 Firebase Console 中，選擇你的專案
2. 在左側邊欄選擇「Realtime Database」
3. 點擊「建立資料庫」
4. 選擇位置（推薦 `asia-southeast1` 或最近的位置）
5. 選擇「以測試模式啟動」（開發用）
   - 注意：生產環境要設置適當的安全規則

### 3. 配置安全規則

在「Realtime Database」→「規則」中，設置以下規則：

```json
{
  "rules": {
    "mv_projects": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid",
        ".validate": "newData.hasChildren(['title', 'createdAt'])"
      }
    }
  }
}
```

### 4. 獲取 Firebase 配置

1. 在專案設置中選擇「應用程式」
2. 選擇 Web 應用程式 (`</>`)
3. 複製 Firebase 配置對象，包含以下欄位：
   - `apiKey`
   - `authDomain`
   - `projectId`
   - `storageBucket`
   - `messagingSenderId`
   - `appId`
   - `measurementId`

### 5. 配置環境變數

1. 複製 `.env.example` 為 `.env.local`
2. 填入上面獲取的 Firebase 配置值

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
# ... 其他配置
```

## 數據結構

Firebase Realtime Database 中的 MV 專案數據結構：

```
/mv_projects/
  /{userId}/
    /{projectId}/
      ├── title: string (MV 標題)
      ├── description: string (描述)
      ├── createdAt: timestamp
      ├── updatedAt: timestamp
      ├── status: "planning" | "designing" | "generating" | "published"
      ├── progress:
      │   ├── step_01_lyrics: boolean
      │   ├── step_02_character: boolean
      │   ├── step_03_scenes: boolean
      │   ├── step_04_storyboard: boolean
      │   ├── step_05_upscale: boolean
      │   ├── step_06_video_prompt: boolean
      │   ├── step_07_generation: boolean
      │   ├── step_08_drone: boolean
      │   ├── step_09_lighting: boolean
      │   ├── step_10_assembly: boolean
      │   ├── step_11_packaging: boolean
      │   └── step_12_upload: boolean
      ├── assets:
      │   ├── music_url: string
      │   ├── video_url: string
      │   └── cover_url: string
      └── metadata:
          ├── genre: string
          ├── duration: number (秒)
          ├── tools_used: string[]
          ├── total_cost: number (美元)
          └── youtube_url: string (發布後)
```

## 在 MV 製作中使用 Firebase

### Step 11 - 打包與資產整理

在完成 Step 10（FFmpeg 組裝）後，Firebase 同步會：

1. **保存專案元數據**
   ```
   {
     "title": "My First MV",
     "status": "published",
     "youtube_url": "https://youtube.com/watch?v=...",
     "total_cost": 12.50,
     "tools_used": ["FLUX.1 Dev", "Kling", "SUNO"]
   }
   ```

2. **更新進度**
   ```
   progress.step_11_packaging = true
   progress.step_12_upload = true
   ```

3. **備份重要 URL**
   ```
   assets.video_url = "gs://bucket/mv/my-mv.mp4"
   assets.cover_url = "gs://bucket/mv/cover.png"
   ```

## 可選：Google Cloud Storage 整合

如果想在雲端備份生成的視頻和圖片：

1. 在 Firebase Console 中啟用「Storage」
2. 在 `.env.local` 中設置 `VITE_GCS_BUCKET`
3. 在 Step 11 中配置自動上傳

## 常見問題

**Q: Firebase 免費方案足夠嗎？**

A: 是的，Spark Plan 包含：
- 1 GB 儲存空間
- 100 個並發連接
- 無限制讀寫（但有 CPU 時間限制）

對於個人 MV 製作完全足夠。

**Q: 數據會被保留多久？**

A: 由你控制。只要你不刪除 Firebase 專案，數據會一直保留。

**Q: 可以與他人分享專案進度嗎？**

A: 目前基礎配置只支持個人訪問。要啟用團隊協作，需要：
1. 設置 Firebase Authentication（Email/Google Sign-in）
2. 修改安全規則允許多用戶訪問
3. 添加協作者管理邏輯

## 後續步驟

- 在 mv-guide-website 專案中集成 Firebase 讀取功能
- 在 CLI 工具中添加自動同步命令
- 設置定期備份到 Google Cloud Storage

