import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(os.path.expandvars(r"%LOCALAPPDATA%\flow_auto\chrome_profile"))
PROJECT_URL = "https://flow.google.com/project/6387c1bf-2e3d-41a3-8064-16e31979e506"

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

    # 滾到底部
    for _ in range(10):
        groups = page.locator("main").get_by_role("group")
        if groups.count():
            groups.last.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

    groups = page.locator("main").get_by_role("group")
    print(f"Total groups: {groups.count()}")
    for i in range(groups.count()):
        g = groups.nth(i)
        lbl = g.get_attribute("aria-label") or ""
        txt = g.inner_text().replace('\n', ' | ')
        btns = [b.get_attribute("aria-label") or b.inner_text().replace('\n', ' ') for b in g.locator("button").all()]
        print(f"[{i:02d}] label={lbl!r} | btns={btns[:5]} | txt={txt[:40]}")

    page.screenshot(path="scripts/inspect_bottom.png")
    ctx.close()
