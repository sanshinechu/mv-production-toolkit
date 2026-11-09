import os, sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"

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

        all_tiles = {}
        stale = 0
        last_count = 0
        
        # 逐步滾動尋找所有 group
        for scroll_step in range(15):
            groups = page.locator("main").get_by_role("group")
            count = groups.count()
            for i in range(count):
                label = groups.nth(i).get_attribute("aria-label") or ""
                text = groups.nth(i).inner_text()
                if label and label not in all_tiles:
                    is_video = "play_circle" in text or "video" in label.lower()
                    all_tiles[label] = {
                        "label": label,
                        "is_video": is_video,
                        "text": text.replace("\n", " | ")[:60]
                    }
            if len(all_tiles) == last_count:
                stale += 1
                if stale >= 3:
                    break
            else:
                stale = 0
            last_count = len(all_tiles)
            
            # 向下滾動
            if count > 0:
                groups.last.scroll_into_view_if_needed()
            page.wait_for_timeout(1500)

        print(f"Total unique tiles discovered: {len(all_tiles)}")
        video_idx = 0
        for label, info in all_tiles.items():
            if info["is_video"]:
                print(f"Video [{video_idx}]: {label!r}")
                video_idx += 1
            else:
                print(f"Image / Other: {label!r}")

        ctx.close()

if __name__ == "__main__":
    main()
