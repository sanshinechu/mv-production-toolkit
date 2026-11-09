import os, sys, time, json, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"
OUT_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw")

TARGETS = [
    ("p01", "Children looking into storm drain"),
    ("p02", "Old man and children meeting fai"),
    ("p03", "Children playing in river"),
    ("p04", "Workers on wooden riverside dock"),
    ("p05", "People washing fabrics and splas"),
    ("p06", "p06"),
    ("p07", "p07"),
    ("p08", "p08"),
    ("p09", "Children and fairy exploring map"),
    ("p10", "Children high-five in computer lab"),
]

def open_browser(pw):
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
    return ctx, page

def download_video_via_url(pw, cut_name, label_prefix, dest_path):
    for attempt in range(1, 4):
        ctx, page = None, None
        try:
            print(f"[{cut_name}] (Attempt {attempt}) Launching browser for {label_prefix!r}...")
            ctx, page = open_browser(pw)
            page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)

            # 滾動尋找目標 tile
            target_tile = None
            for _ in range(15):
                groups = page.locator("main").get_by_role("group")
                for i in range(groups.count()):
                    lbl = groups.nth(i).get_attribute("aria-label") or ""
                    if label_prefix.lower() in lbl.lower():
                        target_tile = groups.nth(i)
                        break
                if target_tile:
                    break
                if groups.count():
                    groups.last.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)

            if not target_tile:
                print(f"  [Attempt {attempt}] Target tile not found: {label_prefix}")
                ctx.close()
                continue

            target_tile.scroll_into_view_if_needed()
            target_tile.hover()
            page.wait_for_timeout(800)

            more_btn = target_tile.get_by_role("button", name="更多選項")
            if more_btn.count() == 0:
                target_tile.hover()
                page.wait_for_timeout(800)
            more_btn.first.click()
            page.wait_for_timeout(800)

            dl_menu = page.get_by_text("下載", exact=True).first
            dl_menu.hover()
            page.wait_for_timeout(800)

            has_1080p = page.locator("role=menuitem").filter(has_text="1080p").count() > 0
            quality_item = page.locator("role=menuitem").filter(has_text="1080p" if has_1080p else "720p").first
            quality_text = "1080p" if has_1080p else "720p"
            print(f"  Found quality: {quality_text}, triggering download request...")

            url = None
            with page.expect_request(
                lambda r: "_upsampled" in r.url or "flow-content.google/video" in r.url or r.url.endswith(".mp4"),
                timeout=20000
            ) as req_info:
                quality_item.click()
            
            url = req_info.value.url
            print(f"  Captured media URL: {url[:80]}...")

            # 使用 urllib 直接下載二進位數據
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=300) as response:
                data = response.read()

            if len(data) < 100_000:
                raise RuntimeError(f"Downloaded file too small: {len(data)} bytes")

            dest_path.write_bytes(data)
            print(f"  Successfully saved {dest_path.name} ({len(data)/1024/1024:.2f} MB, {quality_text})")
            
            try:
                ctx.close()
            except Exception:
                pass
            return True

        except Exception as e:
            print(f"  [Attempt {attempt}] Error: {e}")
            if ctx:
                try: ctx.close()
                except Exception: pass
            time.sleep(2)

    return False

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    with sync_playwright() as pw:
        for cut_name, label_prefix in TARGETS:
            dest_file = OUT_DIR / f"{cut_name}_flow.mp4"
            if dest_file.exists() and dest_file.stat().st_size > 1_000_000:
                print(f"[{cut_name}] Already exists and valid ({dest_file.stat().st_size/1024/1024:.2f} MB), skipping.")
                results[cut_name] = True
                continue
            
            ok = download_video_via_url(pw, cut_name, label_prefix, dest_file)
            results[cut_name] = ok
    
    print("\n=== Download Summary ===")
    for cut_name, ok in results.items():
        print(f"  {cut_name}: {'SUCCESS' if ok else 'FAILED'}")

if __name__ == "__main__":
    main()
