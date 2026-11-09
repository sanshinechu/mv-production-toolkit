import os, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"
OUT_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw")

TARGETS = [
    ("p05", "People washing fabrics and splas"),
    ("p06", "p06"),
    ("p09", "Children and fairy exploring map"),
]

def main():
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

        for cut_name, label_prefix in TARGETS:
            dest_file = OUT_DIR / f"{cut_name}_flow.mp4"
            print(f"\n=== Investigating [{cut_name}] (match {label_prefix!r}) ===")
            
            # 滾動尋找目標影片 tile
            found_tile = None
            for _ in range(15):
                groups = page.locator("main").get_by_role("group")
                for i in range(groups.count()):
                    t = groups.nth(i)
                    lbl = t.get_attribute("aria-label") or ""
                    txt = t.inner_text()
                    # 必須符合名稱且是影片（包含 play_circle）
                    if label_prefix.lower() in lbl.lower() and "play_circle" in txt:
                        found_tile = t
                        print(f"  Found matching video tile: label={lbl!r}")
                        break
                if found_tile:
                    break
                if groups.count():
                    groups.last.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)

            if not found_tile:
                print(f"  [ERROR] Video tile not found for {cut_name}")
                continue

            found_tile.scroll_into_view_if_needed()
            found_tile.hover()
            page.wait_for_timeout(1000)

            more_btn = found_tile.get_by_role("button", name="更多選項")
            if more_btn.count() == 0:
                print("  '更多選項' button not found via role, trying hover again")
                found_tile.hover()
                page.wait_for_timeout(1000)
            
            more_btn.first.click()
            page.wait_for_timeout(1000)

            # 抓出選單中所有項目
            menu_items = page.get_by_role("menuitem").all()
            print(f"  Menu items count: {len(menu_items)}")
            for m in menu_items:
                print(f"    - {m.inner_text()!r}")

            dl_menu = page.get_by_text("下載", exact=True).first
            dl_menu.hover()
            page.wait_for_timeout(1000)

            sub_items = page.get_by_role("menuitem").all()
            print(f"  Submenu items:")
            for m in sub_items:
                print(f"    * {m.inner_text()!r}")

            # 嘗試同時監聽 request 與 download
            captured_url = None
            def on_request(req):
                nonlocal captured_url
                if "flow-content.google/video" in req.url or "_upsampled" in req.url or req.url.endswith(".mp4"):
                    captured_url = req.url

            page.on("request", on_request)
            
            # 尋找 1080p 或 720p
            target_quality = page.locator("role=menuitem").filter(has_text="1080p")
            if target_quality.count() == 0:
                target_quality = page.locator("role=menuitem").filter(has_text="720p")

            if target_quality.count() > 0:
                print(f"  Clicking {target_quality.first.inner_text()!r}")
                # 使用 try catch 同時等 download 或 request
                try:
                    with page.expect_download(timeout=10000) as dl_info:
                        target_quality.first.click()
                    download = dl_info.value
                    download.save_as(str(dest_file))
                    print(f"  SUCCESS via expect_download: {dest_file.name} ({dest_file.stat().st_size/1024/1024:.2f} MB)")
                except Exception as e_dl:
                    print(f"  expect_download timeout, checking captured_url: {captured_url}")
                    if captured_url:
                        req = urllib.request.Request(
                            captured_url,
                            headers={"User-Agent": "Mozilla/5.0"}
                        )
                        with urllib.request.urlopen(req, timeout=300) as response:
                            dest_file.write_bytes(response.read())
                        print(f"  SUCCESS via captured_url: {dest_file.name} ({dest_file.stat().st_size/1024/1024:.2f} MB)")
                    else:
                        print(f"  Failed: {e_dl}")
            
            page.remove_listener("request", on_request)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

        ctx.close()

if __name__ == "__main__":
    main()
