#!/usr/bin/env python3
"""
YouTube Data API v3 — 憑證設定與首次授權工具
作者：阿亮老師・3A科技研究社

用法：
  python setup_credentials.py           # 互動式引導設定流程
  python setup_credentials.py --auth    # 直接執行 OAuth2 授權流程
  python setup_credentials.py --check   # 檢查憑證狀態
"""

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

# ── 路徑設定 ──────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = SKILL_DIR / "credentials"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

# ── YouTube API 所需的 OAuth2 範圍 ─────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def check_dependencies() -> bool:
    """檢查必要套件是否已安裝。"""
    missing = []
    try:
        import google.auth  # noqa: F401
    except ImportError:
        missing.append("google-auth")
    try:
        import google_auth_oauthlib  # noqa: F401
    except ImportError:
        missing.append("google-auth-oauthlib")
    try:
        import googleapiclient  # noqa: F401
    except ImportError:
        missing.append("google-api-python-client")
    try:
        import google.auth.transport.requests  # noqa: F401
    except ImportError:
        missing.append("google-auth-httplib2")

    if missing:
        print("=" * 60)
        print("  缺少必要套件，請執行以下指令安裝：")
        print("  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        print(f"\n  缺少的套件：{', '.join(missing)}")
        print("=" * 60)
        return False
    return True


def check_status():
    """檢查並印出目前的憑證狀態。"""
    print("\n" + "=" * 60)
    print("  YouTube API 憑證狀態檢查")
    print("=" * 60)

    # 檢查套件
    deps_ok = check_dependencies()
    print(f"\n  Python 套件：{'已安裝' if deps_ok else '缺少（見上方）'}")

    # 檢查 client_secrets.json
    if CLIENT_SECRETS_FILE.exists():
        print(f"  client_secrets.json：已存在 ({CLIENT_SECRETS_FILE})")
        try:
            data = json.loads(CLIENT_SECRETS_FILE.read_text(encoding="utf-8"))
            if "installed" in data or "web" in data:
                print("    格式正確（OAuth2 客戶端憑證）")
            else:
                print("    ⚠ 格式可能不正確，請確認是 OAuth2 客戶端 ID 類型")
        except json.JSONDecodeError:
            print("    ⚠ JSON 格式錯誤")
    else:
        print("  client_secrets.json：尚未設定")

    # 檢查 token.json
    if TOKEN_FILE.exists():
        print(f"  token.json：已存在 ({TOKEN_FILE})")
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            if creds.valid:
                print("    權杖有效")
            elif creds.expired and creds.refresh_token:
                print("    權杖已過期，但可自動重新整理")
            else:
                print("    權杖無效，需重新授權")
        except Exception as e:
            print(f"    無法驗證權杖：{e}")
    else:
        print("  token.json：尚未授權")

    print("=" * 60)


def interactive_guide():
    """互動式引導使用者完成 Google Cloud Console 設定。"""
    print("\n" + "=" * 60)
    print("  YouTube Data API v3 — 首次設定引導")
    print("  作者：阿亮老師・3A科技研究社")
    print("=" * 60)

    print("""
此工具將引導您完成以下步驟：

  步驟 1：建立 Google Cloud 專案
  步驟 2：啟用 YouTube Data API v3
  步驟 3：設定 OAuth 同意畫面
  步驟 4：建立 OAuth2 客戶端 ID
  步驟 5：下載 client_secrets.json
  步驟 6：完成首次 OAuth2 授權

詳細圖文教學請參閱：
  references/google_api_setup.md
""")

    input("按 Enter 開始...")

    # ── 步驟 1：建立專案 ──
    print("\n── 步驟 1/6：建立 Google Cloud 專案 ──")
    print("  請前往 Google Cloud Console 建立新專案")
    url = "https://console.cloud.google.com/projectcreate"
    print(f"  網址：{url}")
    choice = input("  是否開啟瀏覽器？(Y/n) ").strip().lower()
    if choice != "n":
        webbrowser.open(url)
    input("  建立完成後按 Enter 繼續...")

    # ── 步驟 2：啟用 API ──
    print("\n── 步驟 2/6：啟用 YouTube Data API v3 ──")
    url = "https://console.cloud.google.com/apis/library/youtube.googleapis.com"
    print(f"  請前往以下網址，點擊「啟用」按鈕：")
    print(f"  網址：{url}")
    choice = input("  是否開啟瀏覽器？(Y/n) ").strip().lower()
    if choice != "n":
        webbrowser.open(url)
    input("  啟用完成後按 Enter 繼續...")

    # ── 步驟 3：OAuth 同意畫面 ──
    print("\n── 步驟 3/6：設定 OAuth 同意畫面 ──")
    url = "https://console.cloud.google.com/apis/credentials/consent"
    print("  請前往設定 OAuth 同意畫面：")
    print(f"  網址：{url}")
    print("""
  設定重點：
    - User Type 選擇「外部」(External)
    - 填寫應用程式名稱（如 "YouTube Uploader"）
    - 填寫您的 Email
    - 新增範圍 (Scopes)：
      * youtube.upload
      * youtube.force-ssl
      * youtube.readonly
    - 新增測試使用者：加入您自己的 Gmail
    - 儲存並繼續
""")
    choice = input("  是否開啟瀏覽器？(Y/n) ").strip().lower()
    if choice != "n":
        webbrowser.open(url)
    input("  設定完成後按 Enter 繼續...")

    # ── 步驟 4：建立 OAuth2 客戶端 ID ──
    print("\n── 步驟 4/6：建立 OAuth2 客戶端 ID ──")
    url = "https://console.cloud.google.com/apis/credentials/oauthclient"
    print("  請前往建立 OAuth 客戶端 ID：")
    print(f"  網址：{url}")
    print("""
  設定重點：
    - 應用程式類型選擇「電腦版應用程式」(Desktop app)
    - 名稱可自訂（如 "YouTube Uploader Desktop"）
    - 點擊「建立」
""")
    choice = input("  是否開啟瀏覽器？(Y/n) ").strip().lower()
    if choice != "n":
        webbrowser.open(url)
    input("  建立完成後按 Enter 繼續...")

    # ── 步驟 5：下載 client_secrets.json ──
    print("\n── 步驟 5/6：下載 client_secrets.json ──")
    print("""
  在剛建立的 OAuth 客戶端 ID 右側，點擊「下載」圖示（下載 JSON）。

  下載後請將檔案放到以下路徑：
""")
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"    {CLIENT_SECRETS_FILE}")

    # 嘗試讓使用者直接輸入路徑
    while True:
        src = input("\n  請輸入已下載的 JSON 檔案路徑（或直接按 Enter 若已手動複製）：").strip().strip('"').strip("'")
        if not src:
            if CLIENT_SECRETS_FILE.exists():
                print("  已偵測到 client_secrets.json！")
                break
            else:
                print(f"  ⚠ 找不到 {CLIENT_SECRETS_FILE}")
                print("  請手動將檔案複製到上述路徑，或重新輸入路徑。")
                retry = input("  重試？(Y/n) ").strip().lower()
                if retry == "n":
                    print("  跳過此步驟，請稍後手動設定。")
                    break
        else:
            src_path = Path(src)
            if src_path.exists():
                import shutil
                CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_path), str(CLIENT_SECRETS_FILE))
                print(f"  已複製到 {CLIENT_SECRETS_FILE}")
                break
            else:
                print(f"  ⚠ 找不到檔案：{src_path}")

    # ── 步驟 6：首次授權 ──
    if CLIENT_SECRETS_FILE.exists():
        print("\n── 步驟 6/6：首次 OAuth2 授權 ──")
        print("  即將開啟瀏覽器進行 Google 帳號授權...")
        choice = input("  是否立即執行？(Y/n) ").strip().lower()
        if choice != "n":
            run_auth_flow()
        else:
            print("  稍後可執行：python setup_credentials.py --auth")
    else:
        print("\n  ⚠ 尚未設定 client_secrets.json，無法進行授權。")
        print("  請完成步驟 5 後再執行：python setup_credentials.py --auth")

    print("\n" + "=" * 60)
    print("  設定流程結束！")
    print("=" * 60)


def run_auth_flow():
    """執行 OAuth2 授權流程，取得並儲存 token。"""
    if not check_dependencies():
        sys.exit(1)

    if not CLIENT_SECRETS_FILE.exists():
        print(f"\n  錯誤：找不到 {CLIENT_SECRETS_FILE}")
        print("  請先執行引導設定：python setup_credentials.py")
        sys.exit(1)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # 如果已有 token，嘗試重新整理
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if creds and creds.valid:
        print("\n  權杖仍然有效，無需重新授權。")
        return creds

    if creds and creds.expired and creds.refresh_token:
        print("\n  權杖已過期，正在自動重新整理...")
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            print("  權杖已重新整理並儲存。")
            return creds
        except Exception as e:
            print(f"  重新整理失敗：{e}")
            print("  將進行完整授權流程...")

    # 完整 OAuth2 授權流程
    print("\n  正在啟動 OAuth2 授權流程...")
    print("  瀏覽器將開啟 Google 登入頁面，請授權存取您的 YouTube 帳號。")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE), SCOPES
    )
    creds = flow.run_local_server(
        port=8080,
        prompt="consent",
        success_message="授權成功！您可以關閉此頁面。",
    )

    # 儲存 token
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"\n  授權成功！權杖已儲存至 {TOKEN_FILE}")

    # 驗證：取得頻道資訊
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.channels().list(part="snippet", mine=True).execute()
        if response.get("items"):
            channel = response["items"][0]["snippet"]
            print(f"  已連接頻道：{channel['title']}")
        else:
            print("  ⚠ 此帳號尚未建立 YouTube 頻道。")
    except Exception as e:
        print(f"  ⚠ 無法驗證頻道（但授權已完成）：{e}")

    return creds


def get_authenticated_service():
    """取得已認證的 YouTube API 服務物件（供其他腳本呼叫）。"""
    if not check_dependencies():
        return None

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        else:
            print("  尚未授權或權杖無效，請先執行：")
            print("  python setup_credentials.py --auth")
            return None

    return build("youtube", "v3", credentials=creds)


# ── 主程式 ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YouTube Data API v3 憑證設定工具"
    )
    parser.add_argument(
        "--auth", action="store_true",
        help="直接執行 OAuth2 授權流程"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="檢查目前的憑證狀態"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="測試現有憑證是否能連接 YouTube API，並顯示頻道名稱"
    )
    args = parser.parse_args()

    if args.verify:
        # 驗證憑證：呼叫 channels().list(mine=True)
        print("\n  驗證 YouTube API 憑證...")
        youtube = get_authenticated_service()
        if youtube is None:
            print("  驗證失敗：無法取得已認證的 API 服務。")
            print("  請先執行：python setup_credentials.py --auth")
            sys.exit(1)
        try:
            response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
            if response.get("items"):
                channel = response["items"][0]
                snippet = channel["snippet"]
                stats = channel.get("statistics", {})
                print(f"  驗證成功！")
                print(f"  頻道名稱：{snippet['title']}")
                print(f"  頻道 ID：{channel['id']}")
                if snippet.get("description"):
                    print(f"  頻道描述：{snippet['description'][:80]}")
                print(f"  訂閱人數：{stats.get('subscriberCount', '未公開')}")
                print(f"  影片總數：{stats.get('videoCount', '未知')}")
                print(f"  總觀看次數：{stats.get('viewCount', '未知')}")
            else:
                print("  驗證成功（API 連線正常），但此帳號尚未建立 YouTube 頻道。")
        except Exception as e:
            print(f"  驗證失敗：{e}")
            sys.exit(1)
    elif args.check:
        check_status()
    elif args.auth:
        run_auth_flow()
    else:
        interactive_guide()
