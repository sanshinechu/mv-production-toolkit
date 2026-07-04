#!/usr/bin/env python3
"""
YouTube 批次上傳工具
作者：阿亮老師・3A科技研究社

用法 A — 從資料夾上傳所有影片：
  python batch_upload.py --folder /path/to/videos --privacy unlisted --category 27

用法 B — 使用 CSV 控制檔：
  python batch_upload.py --csv batch_config.csv

CSV 格式：
  file,title,description,tags,privacy,category
  video1.mp4,第一集標題,描述內容,"AI,教學",public,27
  video2.mp4,第二集標題,描述內容,"Python,教學",unlisted,27

額外選項：
  --delay N         每支影片上傳間隔秒數（預設 10）
  --playlist NAME   上傳後全部加入指定播放清單
  --dry-run         只顯示要上傳的清單，不實際上傳
"""

import argparse
import csv
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

# ── 檢查必要套件 ─────────────────────────────────────────────
try:
    import googleapiclient  # noqa: F401
except ImportError:
    print("\n  錯誤：缺少必要的 Google API 套件。請執行以下指令安裝：")
    print("  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

VALID_EXTENSIONS = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".3gp"}


def parse_args():
    parser = argparse.ArgumentParser(description="YouTube 批次上傳工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--folder", help="包含影片檔案的資料夾路徑")
    group.add_argument("--csv", help="CSV 控制檔路徑")

    parser.add_argument("--privacy", default="private",
                        choices=["public", "unlisted", "private"],
                        help="預設隱私設定（預設 private）")
    parser.add_argument("--category", default="22", help="預設類別 ID（預設 22）")
    parser.add_argument("--tags", default="", help="預設標籤（逗號分隔）")
    parser.add_argument("--description", default="", help="預設描述")
    parser.add_argument("--playlist", default="", help="上傳後全部加入指定播放清單名稱")
    parser.add_argument("--delay", type=int, default=10,
                        help="每支影片上傳間隔秒數（預設 10）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只顯示要上傳的清單，不實際上傳")
    return parser.parse_args()


def validate_credentials():
    """在批次上傳前先驗證 API 憑證是否可用。"""
    from setup_credentials import get_authenticated_service, CLIENT_SECRETS_FILE

    # 檢查 client_secrets.json
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

    # 嘗試取得已認證的服務
    print("  正在驗證 API 憑證...")
    youtube = get_authenticated_service()
    if youtube is None:
        print("\n  錯誤：API 憑證無效或尚未授權。")
        print("  請先執行：python setup_credentials.py --auth")
        sys.exit(1)
    print("  API 憑證驗證成功！\n")
    return youtube


def collect_from_folder(folder_path, defaults):
    """從資料夾收集影片檔案，自動以檔名作為標題。"""
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        print(f"  錯誤：找不到資料夾 {folder}")
        sys.exit(1)

    files = sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
    )

    if not files:
        print(f"  在 {folder} 中找不到影片檔案。")
        print(f"  支援的格式：{', '.join(VALID_EXTENSIONS)}")
        sys.exit(1)

    tasks = []
    for f in files:
        tasks.append({
            "file": str(f),
            "title": f.stem,  # 檔名去副檔名作為標題
            "description": defaults["description"],
            "tags": defaults["tags"],
            "privacy": defaults["privacy"],
            "category": defaults["category"],
        })
    return tasks


def collect_from_csv(csv_path, defaults):
    """從 CSV 控制檔讀取上傳清單。"""
    csv_file = Path(csv_path).resolve()
    if not csv_file.exists():
        print(f"  錯誤：找不到 CSV 檔案 {csv_file}")
        sys.exit(1)

    tasks = []
    csv_dir = csv_file.parent  # CSV 中的相對路徑以此為基準

    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # 驗證必要欄位
        if "file" not in reader.fieldnames:
            print("  錯誤：CSV 必須包含 'file' 欄位。")
            print(f"  偵測到的欄位：{reader.fieldnames}")
            sys.exit(1)

        for row_num, row in enumerate(reader, 2):
            file_path = Path(row["file"])
            # 相對路徑以 CSV 檔案所在目錄為基準，再轉為絕對路徑
            if not file_path.is_absolute():
                file_path = (csv_dir / file_path).resolve()
            else:
                file_path = file_path.resolve()

            if not file_path.exists():
                print(f"  ⚠ 第 {row_num} 行：找不到 {file_path}，跳過。")
                continue

            tasks.append({
                "file": str(file_path),
                "title": row.get("title", file_path.stem) or file_path.stem,
                "description": row.get("description", defaults["description"]) or defaults["description"],
                "tags": row.get("tags", defaults["tags"]) or defaults["tags"],
                "privacy": row.get("privacy", defaults["privacy"]) or defaults["privacy"],
                "category": row.get("category", defaults["category"]) or defaults["category"],
            })

    return tasks


def main():
    args = parse_args()

    defaults = {
        "privacy": args.privacy,
        "category": args.category,
        "tags": args.tags,
        "description": args.description,
    }

    # 在處理任何檔案前，先驗證 API 憑證
    validate_credentials()

    # 收集上傳任務
    if args.folder:
        tasks = collect_from_folder(args.folder, defaults)
    else:
        tasks = collect_from_csv(args.csv, defaults)

    if not tasks:
        print("  沒有要上傳的影片。")
        return

    # 顯示上傳計畫
    print("\n" + "=" * 70)
    print("  YouTube 批次上傳計畫")
    print("=" * 70)
    print(f"\n  共 {len(tasks)} 支影片待上傳：\n")

    total_size = 0
    for i, task in enumerate(tasks, 1):
        fpath = Path(task["file"])
        size = fpath.stat().st_size / (1024 * 1024)
        total_size += size
        print(f"  {i:>3}. {fpath.name}")
        print(f"       標題：{task['title']}")
        print(f"       大小：{size:.1f} MB | 隱私：{task['privacy']} | 類別：{task['category']}")
        if task["tags"]:
            print(f"       標籤：{task['tags']}")

    print(f"\n  總大小：{total_size:.1f} MB")
    if args.playlist:
        print(f"  全部加入播放清單：{args.playlist}")
    print("=" * 70)

    if args.dry_run:
        print("\n  [DRY RUN] 僅顯示計畫，未實際上傳。")
        return

    # 確認
    confirm = input("\n  確認開始上傳？(y/N) ").strip().lower()
    if confirm != "y":
        print("  已取消。")
        return

    # 匯入上傳函式
    from upload_video import upload_via_api

    # 逐一上傳
    results = []
    start_time = time.time()

    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*70}")
        print(f"  [{i}/{len(tasks)}] 上傳中：{Path(task['file']).name}")
        print(f"{'='*70}")

        # 建立模擬的 args 物件
        class UploadArgs:
            pass

        upload_args = UploadArgs()
        upload_args.file = task["file"]
        upload_args.title = task["title"]
        upload_args.description = task["description"]
        upload_args.tags = task["tags"]
        upload_args.category = task["category"]
        upload_args.privacy = task["privacy"]
        upload_args.playlist = args.playlist
        upload_args.thumbnail = ""
        upload_args.method = "api"

        try:
            video_id = upload_via_api(upload_args)
            results.append({
                "file": task["file"],
                "title": task["title"],
                "video_id": video_id,
                "status": "成功" if video_id else "失敗",
            })
        except Exception as e:
            print(f"  上傳失敗：{e}")
            results.append({
                "file": task["file"],
                "title": task["title"],
                "video_id": None,
                "status": f"失敗：{e}",
            })

        # 間隔等待（最後一支不等）
        if i < len(tasks) and args.delay > 0:
            print(f"\n  等待 {args.delay} 秒後上傳下一支...")
            time.sleep(args.delay)

    # 最終報告
    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["video_id"])
    failed = len(results) - success

    print(f"\n{'='*70}")
    print(f"  批次上傳完成！")
    print(f"{'='*70}")
    print(f"  成功：{success} 支 | 失敗：{failed} 支 | 總耗時：{elapsed:.0f} 秒")
    print(f"\n  上傳結果：\n")

    for i, r in enumerate(results, 1):
        fname = Path(r["file"]).name
        if r["video_id"]:
            print(f"  {i:>3}. [成功] {fname}")
            print(f"       https://youtu.be/{r['video_id']}")
        else:
            print(f"  {i:>3}. [失敗] {fname}")
            print(f"       {r['status']}")

    # 儲存報告
    report_path = SKILL_DIR / f"batch_report_{int(time.time())}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"YouTube 批次上傳報告\n")
        f.write(f"時間：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"成功：{success} / {len(results)}\n\n")
        for r in results:
            status = f"https://youtu.be/{r['video_id']}" if r["video_id"] else r["status"]
            f.write(f"{r['title']} | {status}\n")

    print(f"\n  報告已儲存至：{report_path}")


if __name__ == "__main__":
    main()
