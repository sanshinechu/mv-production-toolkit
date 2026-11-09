import os, sys, time, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"
OUT_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw")

MAPPING = [
    ("p01", ["storm drain", "p01"]),
    ("p02", ["meeting fairy", "master dong", "apo", "p02"]),
    ("p03", ["playing in river", "ashe", "p03"]),
    ("p04", ["dock", "riverside dock", "p04"]),
    ("p05", ["washing fabrics", "washing", "p05"]),
    ("p06", ["dragon boat", "dragon", "p06"]),
    ("p07", ["reading album", "old man reading", "p07"]),
    ("p08", ["crane lowering", "slab", "p08"]),
    ("p09", ["exploring map", "map", "p09"]),
    ("p10", ["computer lab", "high-five", "p10"]),
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
        print("Navigating to Flow project...")
        page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(6000)

        groups = page.locator("main").get_by_role("group")
        count = groups.count()
        print(f"Total groups found in main: {count}")
        
        tiles = []
        for i in range(count):
            label = groups.nth(i).get_attribute("aria-label") or ""
            text = groups.nth(i).inner_text()
            tiles.append({"idx": i, "label": label, "text": text.replace("\n", " | ")})
            print(f"[{i}] label={label!r} | text={text.replace(chr(10), ' | ')[:80]}")

        ctx.close()

if __name__ == "__main__":
    main()
