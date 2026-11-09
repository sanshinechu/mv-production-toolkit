import os, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"
OUT_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw")

def download_one(cut_name, group_name):
    dest_file = OUT_DIR / f"{cut_name}_flow.mp4"
    print(f"\n==========================================")
    print(f"Targeting: [{cut_name}] group name={group_name!r}")
    print(f"==========================================")
    
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE),
            channel="chrome",
            headless=True,
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled", "--hide-crash-restore-bubble"]
        )
        page = ctx.new_page()
        page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        # 滾動尋找目標
        target_group = None
        for _ in range(15):
            groups = page.locator("main").get_by_role("group")
            for i in range(groups.count()):
                lbl = groups.nth(i).get_attribute("aria-label") or ""
                txt = groups.nth(i).inner_text()
                if group_name.lower() in lbl.lower() and "play_circle" in txt:
                    target_group = groups.nth(i)
                    break
            if target_group:
                break
            if groups.count():
                groups.last.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

        if not target_group:
            print(f"  [ERROR] Group not found for {cut_name}")
            ctx.close()
            return False

        target_group.scroll_into_view_if_needed()
        target_group.hover()
        page.wait_for_timeout(800)

        # 點擊「更多選項」按鈕（加 force=True）
        more_btn = target_group.get_by_role("button", name="更多選項")
        if more_btn.count() > 0:
            more_btn.first.click(force=True)
        else:
            target_group.locator("button[aria-label='更多選項']").first.click(force=True)
        page.wait_for_timeout(1000)

        dl_menu = page.get_by_text("下載", exact=True).first
        dl_menu.hover()
        page.wait_for_timeout(1000)

        captured_urls = []
        def on_request(req):
            u = req.url
            if any(k in u for k in ["video", "download", "blob", "google", "mp4"]):
                captured_urls.append(u)

        page.on("request", on_request)
        
        target_quality = page.locator("role=menuitem").filter(has_text="1080p")
        if target_quality.count() == 0:
            target_quality = page.locator("role=menuitem").filter(has_text="720p")

        if target_quality.count() > 0:
            q_text = target_quality.first.inner_text()
            print(f"  Found quality item: {q_text!r}")
            
            # 同時監聽 expect_download 和 request
            try:
                with page.expect_download(timeout=10000) as dl_info:
                    target_quality.first.click(force=True)
                download = dl_info.value
                download.save_as(str(dest_file))
                print(f"  SUCCESS via expect_download: {dest_file.name} ({dest_file.stat().st_size/1024/1024:.2f} MB)")
                try: ctx.close()
                except Exception: pass
                return True
            except Exception as e_dl:
                print(f"  expect_download timeout, checking captured requests ({len(captured_urls)} urls captured)...")
                video_url = None
                for u in captured_urls:
                    if "flow-content.google/video" in u or "_upsampled" in u or ".mp4" in u:
                        video_url = u
                        break
                if video_url:
                    print(f"  Found video url: {video_url[:80]}...")
                    req = urllib.request.Request(
                        video_url,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req, timeout=300) as response:
                        dest_file.write_bytes(response.read())
                    print(f"  SUCCESS via captured url: {dest_file.name} ({dest_file.stat().st_size/1024/1024:.2f} MB)")
                    try: ctx.close()
                    except Exception: pass
                    return True
                else:
                    print(f"  No valid video url in captured list:")
                    for u in captured_urls[:10]:
                        print(f"    - {u[:100]}")
        
        try: ctx.close()
        except Exception: pass
        return False

def main():
    ok_09 = download_one("p09", "Children and fairy exploring map")
    print(f"Result p09: {ok_09}")
    time.sleep(3)
    ok_06 = download_one("p06", "p06")
    print(f"Result p06: {ok_06}")

if __name__ == "__main__":
    main()
