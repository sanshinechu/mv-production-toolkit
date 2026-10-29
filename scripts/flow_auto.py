# -*- coding: utf-8 -*-
r"""🅱 Google Flow 網頁自動化（Playwright 操作本機 Chrome；分流規則見 docs/影片分流策略.md）。

用法（cmd）：
  python scripts/flow_auto.py login                       # 開專用 Chrome，老師手動登入 Gmail 帳號一次（看到「新增專案」自動結束）
  python scripts/flow_auto.py inspect                     # 只讀介面、不按生成：存 aria 結構＋截圖到 _flow_inspect/
  python scripts/flow_auto.py run jobs.json --out <資料夾>          # 預演：上傳、設定、貼提示詞，但不按送出
  python scripts/flow_auto.py run jobs.json --out <資料夾> --go     # 真的送出、等生成、下載 1080p

jobs.json：[{"cut": "cut04", "first": "<專案>/分鏡圖/cut04_first.png", "prompt": "...", "seconds": 4}, ...]

- 登入只在 login 由老師自己做，程式不碰帳密；登入狀態存在本機 %LOCALAPPDATA%\flow_auto\chrome_profile（不放 Drive）。
- 一次只跑一鏡，等它生完（或失敗）才送下一鏡；失敗就記錄原因並停下，不自動重試（Flow 會自己退點）。
- 介面定位依 2026-10-27 老師錄影整理，Flow 改版會失效；失效時先跑 inspect 對照再修。
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
PROFILE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "flow_auto" / "chrome_profile"
FLOW = "https://flow.google.com/"
SECONDS = (4, 6, 8, 10)
GEN_TIMEOUT = 15 * 60


def now():
    return dt.datetime.now().strftime("%H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}", flush=True)


def open_browser(pw, headless=False):
    PROFILE.mkdir(parents=True, exist_ok=True)
    ctx = pw.chromium.launch_persistent_context(
        str(PROFILE), channel="chrome", headless=headless, accept_downloads=True,
        viewport={"width": 1440, "height": 900},
        ignore_default_args=["--enable-automation"],
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def cmd_login(pw, a):
    ctx, page = open_browser(pw)
    page.goto(FLOW)
    log("請在開出來的 Chrome 裡登入 Gmail 帳號；進到 Flow 首頁、看得到「新增專案」就會自動結束（最多等 15 分鐘）。")
    t0 = time.time()
    while time.time() - t0 < 15 * 60:
        time.sleep(3)
        if not ctx.pages:
            sys.exit("Chrome 視窗被關掉了，還沒登入完成。請再跑一次 login，登入完成前不要關視窗")
        for p in ctx.pages:     # 登入過程 Google 可能另開分頁，每一頁都看
            try:
                if "flow.google.com" in p.url and "/about" not in p.url and (
                        "/project/" in p.url or p.get_by_text("新增專案").count()):
                    time.sleep(3)
                    ctx.close()
                    log(f"登入完成，狀態已存在 {PROFILE}")
                    return
            except Exception:
                pass            # 換頁中暫時讀不到
    ctx.close()
    sys.exit("等了 15 分鐘還沒看到 Flow 首頁的「新增專案」，請再跑一次 login")


def dump(page, out, name):
    out.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out / f"{name}.png"))
    (out / f"{name}.aria.txt").write_text(page.locator("body").aria_snapshot(), encoding="utf-8")
    log(f"已存 {name}（截圖＋aria 結構）")


def cmd_inspect(pw, a):
    out = ROOT / "_flow_inspect" / dt.datetime.now().strftime("%Y%m%d_%H%M")
    ctx, page = open_browser(pw)
    page.goto(FLOW)
    page.wait_for_timeout(5000)
    dump(page, out, "1_home")
    if a.project:
        page.goto(a.project)
    else:
        page.get_by_text("新增專案").first.click()
    page.wait_for_timeout(6000)
    dump(page, out, "2_project")
    settings_chip(page).click()
    page.wait_for_timeout(1500)
    dump(page, out, "3_settings")
    for label in ("影片", "影格"):
        page.get_by_text(label, exact=True).first.click()
        page.wait_for_timeout(800)
    dump(page, out, "4_settings_video")
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    dump(page, out, "5_prompt_bar_video")
    page.get_by_role("button", name="新增媒體選單").click()
    page.wait_for_timeout(1200)
    dump(page, out, "6_add_media_menu")
    page.keyboard.press("Escape")
    print(f"\n介面已存到 {out}\n專案網址：{page.url}")
    ctx.close()


# ---- 介面定位（依錄影；inspect 後再校正） ----
def settings_chip(page):
    # 輸入列右下角的設定標籤（aria 名稱「設定觸發條件」；新專案預設顯示「Nano Banana 2.1 x 2」，切到影片才是「影片 · 720p · N 秒」）
    return page.get_by_role("button", name="設定觸發條件")


def prompt_box(page):
    return page.get_by_role("textbox", name="你想製作什麼內容？")


def submit_button(page):
    return page.get_by_role("button", name="開始生成")


def snapshot_counts(page):
    return {"video": page.locator("video").count(), "fail": page.get_by_text("失敗", exact=True).count()}


def choose_settings(page, seconds):
    # 設定面板是一組 radio（2026-10-27 inspect）；新專案預設 x 2，一定要切回 x 1，不然點數加倍
    settings_chip(page).click()
    page.wait_for_timeout(800)
    for label in ("影片", "影格", "16:9", "720p", f"{seconds} 秒", "x 1"):
        page.get_by_role("radio", name=label, exact=True).click()
        page.wait_for_timeout(300)
    model = page.get_by_role("button", name="選取模型系列").inner_text()
    if "Omni 1.1 Flash" not in model:
        raise RuntimeError(f"模型不是 Omni 1.1 Flash：{model!r}")
    cost = page.get_by_role("link", name=re.compile(r"^\d+\s*點$")).first.inner_text()
    page.keyboard.press("Escape")
    chip = settings_chip(page).inner_text()
    if f"{seconds} 秒" not in chip or "x 1" not in chip.replace("x1", "x 1"):
        raise RuntimeError(f"設定沒套上：{chip!r}")
    return int(re.search(r"(\d+)", cost).group(1))


def upload_first_frame(page, img):
    with page.expect_file_chooser() as fc:
        page.get_by_role("button", name="新增媒體選單").click()
        page.get_by_role("menuitem", name="上傳").click()
    fc.value.set_files(str(img))
    # 上傳中的媒體格是 group「檔名」，裡面顯示百分比；等百分比消失才算傳完
    tile = page.get_by_role("group", name=img.name, exact=True).first
    tile.wait_for(state="attached", timeout=60_000)
    t0 = time.time()
    while re.search(r"\d+%", tile.inner_text() or ""):
        if time.time() - t0 > 180:
            raise RuntimeError(f"{img.name} 上傳超過 3 分鐘還沒完成")
        page.wait_for_timeout(1500)
    # 「開始」→「選取畫面圖像」視窗 → 點這張（最新的在最上面）就直接設成首幀、視窗自己關掉
    page.get_by_role("button", name="開始", exact=True).click()
    heading = page.get_by_role("heading", name="選取畫面圖像")
    heading.wait_for(timeout=15_000)
    page.get_by_role("option", name=img.name, exact=True).first.click()
    heading.wait_for(state="detached", timeout=15_000)
    # 「開始」格換成縮圖（aria：img「素材圖像」）才算設好
    page.get_by_role("img", name="素材圖像").first.wait_for(timeout=15_000)
    page.wait_for_timeout(1000)


def wait_result(page, before, timeout=GEN_TIMEOUT):
    """送出後等：多一格「失敗」→ fail；多一支 <video> 且畫面上沒有生成中百分比 → ok（新的一格排在最前面）。"""
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout:
        page.wait_for_timeout(5_000)
        fails = page.get_by_text("失敗", exact=True)
        if fails.count() > before["fail"]:
            msg = fails.first.locator("xpath=..").inner_text().replace("\n", " ")
            return "fail", None, msg[:200]
        pct = page.get_by_text(re.compile(r"^\d+%$"))
        if pct.count():
            p = pct.first.inner_text()
            if p != last:
                log(f"  生成中 {p}")
                last = p
            continue
        if page.locator("video").count() > before["video"]:
            # 每格是 group（名稱＝Flow 自動取的標題），新的排第一格
            return "ok", page.locator("main").get_by_role("group").first, ""
    return "timeout", None, f"超過 {timeout // 60} 分鐘"


def download_1080p(page, tile, dest):
    # 滑到那一格上才會出現 ♡ 和 ⋮（按鈕在格子裡面，最後一顆是 ⋮）；⋮ →「下載」→「1080p 已提升畫質」（錄影 219 秒）
    tile.hover()
    page.wait_for_timeout(800)
    try:
        dump(page, ROOT / "_flow_inspect" / "dl_hover", dest.stem)
        tile.get_by_role("button", name="更多選項").click()
        page.get_by_text("下載", exact=True).first.hover()
        page.wait_for_timeout(800)
        with page.expect_download(timeout=10 * 60_000) as dl:
            page.get_by_text("1080p", exact=True).first.click()
    except Exception:
        dump(page, ROOT / "_flow_inspect" / ("err_dl_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")), dest.stem)
        raise
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        old = dest.parent / "_old" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        old.mkdir(parents=True, exist_ok=True)
        dest.replace(old / dest.name)
    dl.value.save_as(str(dest))


def cmd_run(pw, a):
    jobs = json.loads(Path(a.jobs).read_text(encoding="utf-8"))
    for j in jobs:
        if int(j["seconds"]) not in SECONDS:
            sys.exit(f"{j['cut']} 秒數 {j['seconds']} 不在 Flow 可選的 {SECONDS}")
        if not Path(j["first"]).exists():
            sys.exit(f"{j['cut']} 找不到首幀 {j['first']}")
    out = Path(a.out)
    record = out / "flow_auto_log.jsonl"
    ctx, page = open_browser(pw)
    page.goto(a.project or FLOW)
    page.wait_for_timeout(5000)
    if not a.project:
        page.get_by_text("新增專案").first.click()
        page.wait_for_timeout(6000)
    log(f"專案：{page.url}")
    for j in jobs:
        cut = j["cut"]
        log(f"== {cut}（{j['seconds']} 秒）")
        try:
            cost = choose_settings(page, int(j["seconds"]))   # 先切影片模式，「開始」格才會出現
            upload_first_frame(page, Path(j["first"]))
        except Exception:
            dump(page, ROOT / "_flow_inspect" / ("err_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")), cut)
            ctx.close()
            raise
        log(f"  這一鏡要 {cost} 點")
        box = prompt_box(page)
        box.click()
        box.fill(j["prompt"])
        if not a.go:
            dump(page, ROOT / "_flow_inspect" / ("dry_" + dt.datetime.now().strftime("%Y%m%d_%H%M")), cut)
            log("  預演模式：已填好、截圖存在 _flow_inspect/dry_*，不送出")
            box.fill("")
            continue
        before = snapshot_counts(page)
        submit_button(page).click()
        status, tile, msg = wait_result(page, before)
        rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "cut": cut,
               "seconds": j["seconds"], "cost": cost, "status": status, "msg": msg}
        if status == "ok":
            dest = out / f"{cut}_flow.mp4"
            download_1080p(page, tile, dest)
            rec["file"] = str(dest)
            log(f"  完成，已下載 {dest}")
        out.mkdir(parents=True, exist_ok=True)
        with record.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if status != "ok":
            log(f"  {cut} {status}：{msg}——停下，不自動重試")
            break
    ctx.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    p = sub.add_parser("inspect")
    p.add_argument("--project", help="現有專案網址；不給就按「新增專案」")
    p = sub.add_parser("run")
    p.add_argument("jobs")
    p.add_argument("--out", required=True, help="影片下載到哪（例如 <專案>\\videos-raw\\flow；專案搬到當台封存區就給該處的絕對路徑）")
    p.add_argument("--project", help="沿用現有專案網址")
    p.add_argument("--go", action="store_true", help="真的送出（會扣 Flow 點數）；不加就只預演")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        {"login": cmd_login, "inspect": cmd_inspect, "run": cmd_run}[a.cmd](pw, a)


if __name__ == "__main__":
    main()
