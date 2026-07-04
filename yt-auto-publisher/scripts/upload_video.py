#!/usr/bin/env python3
"""
YouTube 影片上傳工具 — 透過 YouTube Data API v3 上傳
作者：阿亮老師・3A科技研究社

用法：
  python upload_video.py --file video.mp4 --title "標題" --description "描述" \\
      --tags "AI,教學" --privacy public --category 27

完整參數：
  --file        影片檔案路徑（必填）
  --title       影片標題（必填）
  --description 影片描述
  --tags        標籤，逗號分隔
  --category    類別 ID（預設 22 = People & Blogs）
  --privacy     public / unlisted / private（預設 private）
  --playlist    上傳後加入指定播放清單名稱
  --thumbnail   自訂縮圖圖片路徑
"""

import argparse
import http.client
import os
import random
import sys
import time
from pathlib import Path

# ── 檢查必要套件 ─────────────────────────────────────────────
try:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("\n  錯誤：缺少必要的 Google API 套件。請執行以下指令安裝：")
    print("  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# ── 路徑設定 ──────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

# ── 常數 ──────────────────────────────────────────────────
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

# 常用類別對照
CATEGORY_MAP = {
    "film": 1, "autos": 2, "music": 10, "pets": 15,
    "sports": 17, "travel": 19, "gaming": 20, "blogs": 22,
    "people": 22, "comedy": 23, "entertainment": 24,
    "news": 25, "howto": 26, "education": 27, "science": 28,
}


def parse_args():
    parser = argparse.ArgumentParser(description="YouTube 影片上傳工具")
    parser.add_argument("--file", required=True, help="影片檔案路徑")
    parser.add_argument("--title", required=True, help="影片標題")
    parser.add_argument("--description", default="", help="影片描述")
    parser.add_argument("--tags", default="", help="標籤，逗號分隔")
    parser.add_argument("--category", default="22", help="類別 ID 或名稱（預設 22）")
    parser.add_argument(
        "--privacy", default="private",
        choices=["public", "unlisted", "private"],
        help="隱私設定（預設 private）",
    )
    parser.add_argument("--playlist", default="", help="上傳後加入指定播放清單名稱")
    parser.add_argument("--thumbnail", default="", help="自訂縮圖圖片路徑")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="模擬執行：驗證檔案、憑證、中繼資料，但不實際上傳",
    )
    return parser.parse_args()


# ══════════════════════════════════════════════════════════
#  方法 A：YouTube Data API v3 上傳
# ══════════════════════════════════════════════════════════

def upload_via_api(args):
    """使用 YouTube Data API v3 上傳影片（支援斷點續傳）。"""
    from setup_credentials import get_authenticated_service, CLIENT_SECRETS_FILE

    # 檢查 client_secrets.json 是否存在，提供逐步指引
    if not CLIENT_SECRETS_FILE.exists():
        print("\n  錯誤：找不到 API 憑證檔案 client_secrets.json")
        print("  " + "=" * 55)
        print("  請依照以下步驟設定：")
        print("  1. 前往 https://console.cloud.google.com/")
        print("  2. 建立專案並啟用 YouTube Data API v3")
        print("  3. 建立 OAuth2 客戶端 ID（桌面應用程式）")
        print("  4. 下載 JSON 並放到：")
        print(f"     {CLIENT_SECRETS_FILE}")
        print("  5. 執行：python setup_credentials.py --auth")
        print("  " + "=" * 55)
        print("\n  或直接執行互動式引導：python setup_credentials.py")
        sys.exit(1)

    youtube = get_authenticated_service()
    if youtube is None:
        print("\n  無法取得 YouTube API 服務。請先執行授權設定：")
        print("  python setup_credentials.py --auth")
        sys.exit(1)

    # 解析類別
    category_id = args.category
    if category_id.lower() in CATEGORY_MAP:
        category_id = str(CATEGORY_MAP[category_id.lower()])

    # 解析標籤
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None

    # 建立影片中繼資料
    body = {
        "snippet": {
            "title": args.title,
            "description": args.description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"  錯誤：找不到影片檔案 {file_path}")
        sys.exit(1)

    file_size = file_path.stat().st_size
    print(f"\n  準備上傳：{file_path.name}")
    print(f"  檔案大小：{file_size / (1024*1024):.1f} MB")
    print(f"  標題：{args.title}")
    print(f"  隱私：{args.privacy}")
    print(f"  類別：{category_id}")
    if tags:
        print(f"  標籤：{', '.join(tags)}")

    # 使用 resumable upload（斷點續傳）
    media = MediaFileUpload(
        str(file_path),
        chunksize=10 * 1024 * 1024,  # 10MB 分塊
        resumable=True,
        mimetype="video/*",
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    print("\n  開始上傳...（按 Ctrl+C 可中斷）")
    video_id = _resumable_upload(request, file_size)

    if video_id:
        print(f"\n  上傳成功！")
        print(f"  影片 ID：{video_id}")
        print(f"  影片網址：https://www.youtube.com/watch?v={video_id}")
        print(f"  YouTube Studio：https://studio.youtube.com/video/{video_id}/edit")

        # 設定自訂縮圖
        if args.thumbnail:
            _set_thumbnail(youtube, video_id, args.thumbnail)

        # 加入播放清單
        if args.playlist:
            _add_to_playlist(youtube, video_id, args.playlist)

        return video_id
    return None


def _resumable_upload(request, total_size):
    """執行斷點續傳上傳，顯示進度與錯誤重試。支援 Ctrl+C 中斷。"""
    response = None
    error = None
    retry = 0
    start_time = time.time()
    # 追蹤上傳進度，用於中斷時顯示
    last_uploaded = 0
    last_percent = 0.0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                last_uploaded = status.resumable_progress
                last_percent = (last_uploaded / total_size) * 100
                elapsed = time.time() - start_time
                speed = last_uploaded / elapsed / (1024 * 1024) if elapsed > 0 else 0
                remaining = (total_size - last_uploaded) / (speed * 1024 * 1024) if speed > 0 else 0
                bar = _progress_bar(last_percent)
                print(
                    f"\r  {bar} {last_percent:5.1f}% | "
                    f"{last_uploaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB | "
                    f"{speed:.1f} MB/s | "
                    f"剩餘 {remaining:.0f}s",
                    end="", flush=True,
                )
            if response is not None:
                elapsed = time.time() - start_time
                print(f"\n  上傳耗時：{elapsed:.1f} 秒")
                return response.get("id")
        except KeyboardInterrupt:
            # 使用者按下 Ctrl+C，顯示目前進度並中斷
            print(f"\n\n  上傳已中斷，已完成 {last_percent:.1f}%")
            print(f"  已上傳 {last_uploaded/(1024*1024):.1f} / {total_size/(1024*1024):.1f} MB")
            print("  注意：YouTube API 的 resumable upload 不支援跨程序續傳，需重新上傳。")
            sys.exit(130)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e.content.decode()}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                print(f"\n  錯誤：已超過最大重試次數 ({MAX_RETRIES})")
                sys.exit(1)
            sleep_seconds = random.random() * (2 ** retry)
            print(f"\n  重試 {retry}/{MAX_RETRIES}（等待 {sleep_seconds:.1f}s）：{error}")
            time.sleep(sleep_seconds)
            error = None

    return None


def _progress_bar(percent, width=30):
    """產生文字進度條。"""
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"


def _set_thumbnail(youtube, video_id, thumbnail_path):
    """設定影片自訂縮圖。"""
    thumb = Path(thumbnail_path)
    if not thumb.exists():
        print(f"  ⚠ 找不到縮圖檔案：{thumb}")
        return

    print(f"  設定縮圖：{thumb.name}")
    try:
        media = MediaFileUpload(str(thumb), mimetype="image/jpeg")
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        print("  縮圖設定成功！")
    except Exception as e:
        print(f"  ⚠ 縮圖設定失敗（可能需要頻道通過驗證）：{e}")


def _add_to_playlist(youtube, video_id, playlist_name):
    """將影片加入指定名稱的播放清單。"""
    print(f"  尋找播放清單：{playlist_name}")
    try:
        # 搜尋現有播放清單
        playlists = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50
        ).execute()

        playlist_id = None
        for pl in playlists.get("items", []):
            if pl["snippet"]["title"] == playlist_name:
                playlist_id = pl["id"]
                break

        if not playlist_id:
            print(f"  找不到播放清單「{playlist_name}」，正在建立...")
            new_pl = youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": playlist_name, "description": ""},
                    "status": {"privacyStatus": "public"},
                },
            ).execute()
            playlist_id = new_pl["id"]
            print(f"  已建立播放清單：{playlist_name} ({playlist_id})")

        # 加入影片
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        ).execute()
        print(f"  已將影片加入播放清單「{playlist_name}」")
    except Exception as e:
        print(f"  ⚠ 播放清單操作失敗：{e}")


# ══════════════════════════════════════════════════════════
#  主程式
# ══════════════════════════════════════════════════════════

def dry_run_check(args):
    """模擬執行：驗證所有先決條件但不實際上傳。"""
    print("\n" + "=" * 50)
    print("  模擬執行模式（Dry Run）")
    print("=" * 50)

    errors = []
    warnings = []

    # 1. 檢查影片檔案
    file_path = Path(args.file)
    if file_path.exists():
        file_size = file_path.stat().st_size
        print(f"\n  [v] 影片檔案存在：{file_path}")
        print(f"      大小：{file_size / (1024*1024):.1f} MB")
    else:
        errors.append(f"找不到影片檔案：{file_path}")
        print(f"\n  [X] 影片檔案不存在：{file_path}")

    # 2. 檢查檔案格式
    valid_extensions = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".3gp"}
    if file_path.suffix.lower() in valid_extensions:
        print(f"  [v] 檔案格式有效：{file_path.suffix}")
    else:
        warnings.append(f"檔案格式 {file_path.suffix} 可能不受支援")
        print(f"  [!] 檔案格式可能不受支援：{file_path.suffix}")

    # 3. 驗證中繼資料
    if args.title:
        title_len = len(args.title)
        if title_len <= 100:
            print(f"  [v] 標題有效：{args.title}（{title_len} 字元）")
        else:
            warnings.append(f"標題超過 100 字元（{title_len}），YouTube 可能截斷")
    else:
        errors.append("未提供標題")

    if args.description and len(args.description) > 5000:
        warnings.append(f"描述超過 5000 字元（{len(args.description)}）")

    print(f"  [v] 隱私設定：{args.privacy}")
    print(f"  [v] 類別：{args.category}")

    # 4. 檢查憑證
    from setup_credentials import CLIENT_SECRETS_FILE, TOKEN_FILE
    if CLIENT_SECRETS_FILE.exists():
        print(f"  [v] client_secrets.json 存在")
    else:
        errors.append("找不到 client_secrets.json")
        print(f"  [X] client_secrets.json 不存在")

    if TOKEN_FILE.exists():
        print(f"  [v] token.json 存在")
        # 嘗試驗證 token
        try:
            from setup_credentials import get_authenticated_service
            youtube = get_authenticated_service()
            if youtube:
                response = youtube.channels().list(part="snippet", mine=True).execute()
                if response.get("items"):
                    channel_name = response["items"][0]["snippet"]["title"]
                    print(f"  [v] API 連線成功，頻道：{channel_name}")
                else:
                    warnings.append("API 連線成功但未找到頻道")
            else:
                errors.append("無法取得已認證的 API 服務")
        except Exception as e:
            warnings.append(f"憑證驗證時發生錯誤：{e}")
    else:
        errors.append("找不到 token.json，尚未完成 OAuth2 授權")
        print(f"  [X] token.json 不存在")

    # 5. 檢查縮圖
    if args.thumbnail:
        if Path(args.thumbnail).exists():
            print(f"  [v] 縮圖檔案存在：{args.thumbnail}")
        else:
            warnings.append(f"找不到縮圖檔案：{args.thumbnail}")

    # 結果摘要
    print(f"\n{'=' * 50}")
    if errors:
        print(f"  模擬結果：FAIL（{len(errors)} 個錯誤）")
        for e in errors:
            print(f"    [X] {e}")
    else:
        print(f"  模擬結果：PASS — 所有驗證通過，可以正式上傳")

    if warnings:
        print(f"\n  警告（{len(warnings)} 個）：")
        for w in warnings:
            print(f"    [!] {w}")

    print(f"{'=' * 50}\n")
    sys.exit(1 if errors else 0)


def main():
    args = parse_args()

    # 模擬執行模式
    if args.dry_run:
        dry_run_check(args)
        return

    # 驗證檔案
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"  錯誤：找不到影片檔案 {file_path}")
        sys.exit(1)

    # 驗證檔案格式
    valid_extensions = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".3gp"}
    if file_path.suffix.lower() not in valid_extensions:
        print(f"  警告：{file_path.suffix} 可能不是支援的影片格式。")
        print(f"  支援的格式：{', '.join(valid_extensions)}")

    upload_via_api(args)


if __name__ == "__main__":
    main()
