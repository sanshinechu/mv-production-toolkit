#!/usr/bin/env python3
"""
YouTube 頻道管理工具
作者：阿亮老師・3A科技研究社

用法：
  python manage_channel.py list-videos [--max 50]
  python manage_channel.py update-video --video-id ID --title "新標題" --description "新描述"
  python manage_channel.py list-playlists
  python manage_channel.py create-playlist --title "名稱" --description "描述" --privacy public
  python manage_channel.py add-to-playlist --playlist-id PL_ID --video-id V_ID
  python manage_channel.py remove-from-playlist --playlist-item-id PLI_ID
  python manage_channel.py delete-playlist --playlist-id PL_ID
  python manage_channel.py analytics
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


def get_youtube():
    """取得已認證的 YouTube API 服務。"""
    from setup_credentials import get_authenticated_service
    yt = get_authenticated_service()
    if yt is None:
        print("  無法取得 YouTube API 服務。請先執行：")
        print("  python setup_credentials.py --auth")
        sys.exit(1)
    return yt


# ── 影片管理 ──────────────────────────────────────────────

def list_videos(args):
    """列出頻道所有影片。"""
    youtube = get_youtube()
    print("\n  正在取得影片列表...\n")

    max_results = min(args.max, 50)
    videos = []
    page_token = None

    while len(videos) < args.max:
        response = youtube.search().list(
            part="snippet",
            forMine=True,
            type="video",
            maxResults=max_results,
            pageToken=page_token,
            order="date",
        ).execute()

        for item in response.get("items", []):
            videos.append(item)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    if not videos:
        print("  找不到任何影片。")
        return

    # 取得影片詳細統計（分批處理，每批最多 50 個）
    video_ids = [v["id"]["videoId"] for v in videos]
    stats_map = {}
    for batch_start in range(0, len(video_ids), 50):
        batch_ids = video_ids[batch_start:batch_start + 50]
        stats_response = youtube.videos().list(
            part="statistics,status,contentDetails",
            id=",".join(batch_ids),
        ).execute()
        for v in stats_response.get("items", []):
            stats_map[v["id"]] = v

    print(f"  找到 {len(videos)} 支影片：")
    print("  " + "-" * 90)
    print(f"  {'#':>3}  {'發布日期':<12} {'觀看':>8} {'讚':>6} {'隱私':<8} 標題")
    print("  " + "-" * 90)

    for i, v in enumerate(videos, 1):
        vid = v["id"]["videoId"]
        title = v["snippet"]["title"][:40]
        published = v["snippet"]["publishedAt"][:10]
        stat = stats_map.get(vid, {})
        views = stat.get("statistics", {}).get("viewCount", "?")
        likes = stat.get("statistics", {}).get("likeCount", "?")
        privacy = stat.get("status", {}).get("privacyStatus", "?")
        print(f"  {i:>3}  {published:<12} {views:>8} {likes:>6} {privacy:<8} {title}")
        print(f"       ID: {vid}  https://youtu.be/{vid}")

    print("  " + "-" * 90)
    print(f"  共 {len(videos)} 支影片")


def update_video(args):
    """更新影片中繼資料。"""
    youtube = get_youtube()
    video_id = args.video_id

    # 先取得目前的影片資訊
    current = youtube.videos().list(
        part="snippet,status", id=video_id
    ).execute()

    if not current.get("items"):
        print(f"  錯誤：找不到影片 {video_id}")
        sys.exit(1)

    item = current["items"][0]
    snippet = item["snippet"]
    status = item["status"]

    print(f"\n  正在更新影片：{snippet['title']}")
    print(f"  影片 ID：{video_id}")

    # 更新欄位
    if args.title:
        print(f"  標題：{snippet['title']} -> {args.title}")
        snippet["title"] = args.title
    if args.description is not None:
        print(f"  描述：已更新")
        snippet["description"] = args.description
    if args.tags:
        new_tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(f"  標籤：{new_tags}")
        snippet["tags"] = new_tags
    if args.category:
        print(f"  類別：{args.category}")
        snippet["categoryId"] = args.category
    if args.privacy:
        print(f"  隱私：{status['privacyStatus']} -> {args.privacy}")
        status["privacyStatus"] = args.privacy

    # 執行更新
    youtube.videos().update(
        part="snippet,status",
        body={"id": video_id, "snippet": snippet, "status": status},
    ).execute()

    print("\n  更新成功！")
    print(f"  https://www.youtube.com/watch?v={video_id}")


# ── 播放清單管理 ──────────────────────────────────────────

def list_playlists(args):
    """列出所有播放清單（支援分頁，可處理超過 50 個播放清單）。"""
    youtube = get_youtube()
    print("\n  正在取得播放清單...\n")

    # 使用分頁取得所有播放清單
    playlists = []
    page_token = None

    while True:
        response = youtube.playlists().list(
            part="snippet,contentDetails,status",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        playlists.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    if not playlists:
        print("  沒有播放清單。")
        return

    print(f"  {'#':>3}  {'影片數':>6}  {'隱私':<10} 名稱")
    print("  " + "-" * 70)

    for i, pl in enumerate(playlists, 1):
        title = pl["snippet"]["title"]
        count = pl["contentDetails"]["itemCount"]
        privacy = pl["status"]["privacyStatus"]
        pl_id = pl["id"]
        print(f"  {i:>3}  {count:>6}  {privacy:<10} {title}")
        print(f"       ID: {pl_id}")

    print("  " + "-" * 70)
    print(f"  共 {len(playlists)} 個播放清單")


def create_playlist(args):
    """建立新播放清單。"""
    youtube = get_youtube()

    print(f"\n  建立播放清單：{args.title}")

    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": args.title,
                "description": args.description or "",
            },
            "status": {
                "privacyStatus": args.privacy or "public",
            },
        },
    ).execute()

    pl_id = response["id"]
    print(f"  建立成功！")
    print(f"  播放清單 ID：{pl_id}")
    print(f"  網址：https://www.youtube.com/playlist?list={pl_id}")


def add_to_playlist(args):
    """將影片加入播放清單。"""
    youtube = get_youtube()

    print(f"\n  將影片 {args.video_id} 加入播放清單 {args.playlist_id}")

    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": args.playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": args.video_id,
                },
            }
        },
    ).execute()

    print("  加入成功！")


def remove_from_playlist(args):
    """從播放清單移除項目。"""
    youtube = get_youtube()

    print(f"\n  正在從播放清單移除項目 {args.playlist_item_id}...")
    youtube.playlistItems().delete(id=args.playlist_item_id).execute()
    print("  移除成功！")


def delete_playlist(args):
    """刪除播放清單。"""
    youtube = get_youtube()

    # 確認
    response = youtube.playlists().list(
        part="snippet", id=args.playlist_id
    ).execute()

    if not response.get("items"):
        print(f"  錯誤：找不到播放清單 {args.playlist_id}")
        sys.exit(1)

    title = response["items"][0]["snippet"]["title"]
    confirm = input(f"  確定要刪除播放清單「{title}」？(y/N) ").strip().lower()
    if confirm != "y":
        print("  已取消。")
        return

    youtube.playlists().delete(id=args.playlist_id).execute()
    print(f"  已刪除播放清單「{title}」")


# ── 頻道分析 ──────────────────────────────────────────────

def analytics(args):
    """取得頻道分析摘要。"""
    youtube = get_youtube()

    print("\n  正在取得頻道資訊...\n")

    # 頻道基本資訊
    channel_resp = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        mine=True,
    ).execute()

    if not channel_resp.get("items"):
        print("  找不到頻道資訊。")
        return

    channel = channel_resp["items"][0]
    snippet = channel["snippet"]
    stats = channel["statistics"]

    print("  " + "=" * 50)
    print(f"  頻道名稱：{snippet['title']}")
    if snippet.get("description"):
        desc = snippet["description"][:80]
        print(f"  頻道描述：{desc}{'...' if len(snippet['description']) > 80 else ''}")
    print(f"  建立日期：{snippet['publishedAt'][:10]}")
    print("  " + "-" * 50)
    print(f"  訂閱者數：{int(stats.get('subscriberCount', 0)):,}")
    print(f"  總觀看數：{int(stats.get('viewCount', 0)):,}")
    print(f"  影片數量：{int(stats.get('videoCount', 0)):,}")
    print("  " + "=" * 50)

    # 最近影片統計
    print("\n  最近 10 支影片統計：\n")

    search_resp = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        maxResults=10,
        order="date",
    ).execute()

    video_ids = [v["id"]["videoId"] for v in search_resp.get("items", [])]
    if video_ids:
        detail_resp = youtube.videos().list(
            part="statistics,contentDetails",
            id=",".join(video_ids),
        ).execute()

        total_views = 0
        total_likes = 0
        total_comments = 0

        print(f"  {'發布日期':<12} {'觀看':>10} {'讚':>8} {'留言':>8} 標題")
        print("  " + "-" * 80)

        for item in search_resp.get("items", []):
            vid = item["id"]["videoId"]
            title = item["snippet"]["title"][:35]
            published = item["snippet"]["publishedAt"][:10]

            detail = next(
                (d for d in detail_resp.get("items", []) if d["id"] == vid),
                None,
            )
            if detail:
                s = detail["statistics"]
                views = int(s.get("viewCount", 0))
                likes = int(s.get("likeCount", 0))
                comments = int(s.get("commentCount", 0))
                total_views += views
                total_likes += likes
                total_comments += comments
                print(f"  {published:<12} {views:>10,} {likes:>8,} {comments:>8,} {title}")

        print("  " + "-" * 80)
        print(f"  {'合計':<12} {total_views:>10,} {total_likes:>8,} {total_comments:>8,}")

        if len(video_ids) > 0:
            avg_views = total_views / len(video_ids)
            avg_likes = total_likes / len(video_ids)
            print(f"  {'平均':<12} {avg_views:>10,.0f} {avg_likes:>8,.0f}")

    print()


# ── 主程式 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YouTube 頻道管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用指令")

    # list-videos
    p_lv = subparsers.add_parser("list-videos", help="列出頻道影片")
    p_lv.add_argument("--max", type=int, default=50, help="最多列出幾支（預設 50）")

    # update-video
    p_uv = subparsers.add_parser("update-video", help="更新影片中繼資料")
    p_uv.add_argument("--video-id", required=True, help="影片 ID")
    p_uv.add_argument("--title", help="新標題")
    p_uv.add_argument("--description", help="新描述")
    p_uv.add_argument("--tags", help="新標籤（逗號分隔）")
    p_uv.add_argument("--category", help="新類別 ID")
    p_uv.add_argument("--privacy", choices=["public", "unlisted", "private"], help="新隱私設定")

    # list-playlists
    subparsers.add_parser("list-playlists", help="列出播放清單")

    # create-playlist
    p_cp = subparsers.add_parser("create-playlist", help="建立播放清單")
    p_cp.add_argument("--title", required=True, help="播放清單名稱")
    p_cp.add_argument("--description", default="", help="播放清單描述")
    p_cp.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])

    # add-to-playlist
    p_ap = subparsers.add_parser("add-to-playlist", help="將影片加入播放清單")
    p_ap.add_argument("--playlist-id", required=True, help="播放清單 ID")
    p_ap.add_argument("--video-id", required=True, help="影片 ID")

    # remove-from-playlist
    p_rp = subparsers.add_parser("remove-from-playlist", help="從播放清單移除")
    p_rp.add_argument("--playlist-item-id", required=True, help="播放清單項目 ID")

    # delete-playlist
    p_dp = subparsers.add_parser("delete-playlist", help="刪除播放清單")
    p_dp.add_argument("--playlist-id", required=True, help="播放清單 ID")

    # analytics
    subparsers.add_parser("analytics", help="頻道分析摘要")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    command_map = {
        "list-videos": list_videos,
        "update-video": update_video,
        "list-playlists": list_playlists,
        "create-playlist": create_playlist,
        "add-to-playlist": add_to_playlist,
        "remove-from-playlist": remove_from_playlist,
        "delete-playlist": delete_playlist,
        "analytics": analytics,
    }

    func = command_map.get(args.command)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
