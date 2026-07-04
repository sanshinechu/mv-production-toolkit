---
name: yt-auto-publisher
description: >
  YouTube 影片自動發布技能 — 支援透過 YouTube Data API v3 上傳影片、管理頻道、批次上傳，
  或在未設定 API 時使用瀏覽器自動化作為備援方案。
  觸發情境：上傳 YouTube、YouTube 發布、上傳影片、發布到 YouTube、YouTube upload、
  影片上傳、管理 YouTube 頻道、批次上傳影片、YouTube 頻道管理。
author: 阿亮老師・3A科技研究社
triggers:
  - 上傳 YouTube
  - YouTube 發布
  - 上傳影片
  - 發布到 YouTube
  - YouTube upload
---

# YouTube 自動發布技能

自動化 YouTube 影片上傳與頻道管理。提供兩種方法：API 直連（推薦）與瀏覽器自動化（備援）。

## 環境檢查

使用前請先執行環境檢查，確認套件與憑證皆已就緒：

```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/env_check.py"
```

## 快速測試

驗證憑證是否有效並顯示頻道名稱：

```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/setup_credentials.py" --verify
```

## API 配額預估

| 操作 | 配額消耗 | 每日免費上限 |
|------|----------|-------------|
| 上傳影片 (videos.insert) | 1600 單位 | 約 6 次 |
| 更新中繼資料 (videos.update) | 50 單位 | 約 200 次 |
| 列出影片 (search.list) | 100 單位 | 約 100 次 |
| 播放清單操作 | 50 單位 | 約 200 次 |
| 頻道資訊 (channels.list) | 1 單位 | 約 10000 次 |

> YouTube Data API v3 每日免費配額為 10,000 單位。上傳影片最消耗配額，建議每日不超過 6 支。

---

## 方法選擇

### 方法 A：YouTube Data API v3（推薦）

- 穩定可靠，支援所有功能
- 需要 Google Cloud Console 設定 OAuth2 憑證
- 支援：上傳影片、更新中繼資料、管理播放清單、取得分析摘要
- 前置套件：`google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`

### 方法 B：瀏覽器自動化（備援）

- 不需要 API 設定，直接操作 YouTube Studio
- 使用 Playwright 或 browser-use
- 穩定性較低，YouTube 介面變更時可能失效
- 適合臨時使用或無法設定 API 的情境

---

## 前置檢查（每次使用前必做）

### 1. 確認 Python 環境

```bash
python --version || python3 --version
```

### 2. 安裝必要套件（方法 A）

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### 3. 安裝必要套件（方法 B，備援）

```bash
pip install playwright browser-use
playwright install chromium
```

### 4. 確認憑證狀態

```bash
# 檢查是否已有 OAuth2 憑證
SKILL_DIR="C:/Users/user/.claude/skills/yt-auto-publisher"
if [ -f "$SKILL_DIR/credentials/client_secrets.json" ]; then
  echo "✓ client_secrets.json 已存在"
else
  echo "✗ 尚未設定 client_secrets.json，請先執行 setup_credentials.py"
fi

if [ -f "$SKILL_DIR/credentials/token.json" ]; then
  echo "✓ token.json 已存在（已完成授權）"
else
  echo "✗ 尚未授權，首次使用需完成 OAuth2 流程"
fi
```

---

## 使用流程

### 首次設定（僅需一次）

1. **建立 Google Cloud 專案與 OAuth2 憑證**
   ```bash
   python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/setup_credentials.py"
   ```
   - 腳本會引導你完成 Google Cloud Console 設定
   - 詳細圖文教學見 `references/google_api_setup.md`

2. **將下載的 `client_secrets.json` 放到憑證目錄**
   ```bash
   mkdir -p "C:/Users/user/.claude/skills/yt-auto-publisher/credentials"
   cp /path/to/client_secrets.json "C:/Users/user/.claude/skills/yt-auto-publisher/credentials/"
   ```

3. **完成首次授權**（會開啟瀏覽器登入 Google）
   ```bash
   python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/setup_credentials.py" --auth
   ```

### 上傳單支影片

```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/upload_video.py" \
  --file video.mp4 \
  --title "影片標題" \
  --description "影片描述" \
  --tags "AI,教學,科技" \
  --category 27 \
  --privacy public
```

參數說明：
| 參數 | 必填 | 說明 |
|------|------|------|
| `--file` | 是 | 影片檔案路徑 |
| `--title` | 是 | 影片標題 |
| `--description` | 否 | 影片描述（預設空白） |
| `--tags` | 否 | 標籤，逗號分隔 |
| `--category` | 否 | 類別 ID（預設 22=People & Blogs） |
| `--privacy` | 否 | public / unlisted / private（預設 private） |
| `--playlist` | 否 | 上傳後加入指定播放清單名稱 |
| `--thumbnail` | 否 | 自訂縮圖圖片路徑 |

常用類別 ID：
- 22 = People & Blogs
- 27 = Education（教育）
- 28 = Science & Technology（科學與科技）
- 24 = Entertainment（娛樂）
- 26 = Howto & Style（教學與風格）

### 批次上傳

```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/batch_upload.py" \
  --folder /path/to/videos \
  --privacy unlisted \
  --category 27
```

也支援 CSV 控制檔批次上傳：
```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/batch_upload.py" \
  --csv batch_config.csv
```

CSV 格式：
```csv
file,title,description,tags,privacy,category
video1.mp4,第一集標題,描述內容,"AI,教學",public,27
video2.mp4,第二集標題,描述內容,"Python,教學",unlisted,27
```

### 頻道管理

```bash
# 列出頻道所有影片
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" list-videos

# 更新影片中繼資料
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" update-video \
  --video-id VIDEO_ID \
  --title "新標題" \
  --description "新描述"

# 列出播放清單
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" list-playlists

# 建立播放清單
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" create-playlist \
  --title "播放清單名稱" \
  --description "播放清單描述" \
  --privacy public

# 將影片加入播放清單
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" add-to-playlist \
  --playlist-id PLAYLIST_ID \
  --video-id VIDEO_ID

# 取得頻道分析摘要
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/manage_channel.py" analytics
```

---

## 方法 B：瀏覽器自動化（備援）

當 API 未設定時，可改用瀏覽器自動化上傳：

```bash
python "C:/Users/user/.claude/skills/yt-auto-publisher/scripts/upload_video.py" \
  --method browser \
  --file video.mp4 \
  --title "影片標題" \
  --description "影片描述"
```

注意事項：
- 首次使用需登入 YouTube（瀏覽器會開啟）
- YouTube Studio 介面可能變更導致腳本失效
- 不支援所有 API 方法的功能（如播放清單管理）
- 建議僅作為臨時方案，長期使用請設定 API

---

## 疑難排解

| 問題 | 解法 |
|------|------|
| `token.json` 過期 | 刪除 token.json，重新執行 `setup_credentials.py --auth` |
| 上傳配額超限 | YouTube API 每日配額有限，隔天再試或申請配額增加 |
| 影片處理中 | 上傳後 YouTube 需時間處理，屬正常現象 |
| 403 Forbidden | 確認 API 已啟用，OAuth2 範圍包含 youtube.upload |
| 瀏覽器自動化失敗 | YouTube Studio 介面可能已更新，嘗試更新腳本或改用 API |

---

## 檔案結構

```
yt-auto-publisher/
├── SKILL.md                          # 本文件
├── credentials/                      # 憑證目錄（不可上傳至版控）
│   ├── client_secrets.json           # Google OAuth2 客戶端憑證
│   └── token.json                    # 授權後產生的存取權杖
├── scripts/
│   ├── setup_credentials.py          # 首次設定與授權引導
│   ├── upload_video.py               # 單支影片上傳（API + 瀏覽器備援）
│   ├── manage_channel.py             # 頻道管理（列表、更新、播放清單、分析）
│   └── batch_upload.py               # 批次上傳
└── references/
    └── google_api_setup.md           # Google Cloud Console 設定圖文教學
```
