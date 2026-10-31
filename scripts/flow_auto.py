# -*- coding: utf-8 -*-
r"""🅱 Google Flow 網頁自動化（Playwright 操作本機 Chrome；分流規則見 docs/影片分流策略.md）。

用法（cmd）：
  python scripts/flow_auto.py login                       # 開專用 Chrome，老師手動登入 Gmail 帳號一次（看到「新增專案」自動結束）
  python scripts/flow_auto.py inspect                     # 只讀介面、不按生成：存 aria 結構＋截圖到 _flow_inspect/
  python scripts/flow_auto.py run jobs.json --out <資料夾>          # 預演：上傳、設定、貼提示詞，但不按送出
  python scripts/flow_auto.py run jobs.json --out <資料夾> --project <預演印出的網址> --go
                                                                    # 真的送出、等生成、改名成 cutNN、下載 1080p；
                                                                    # 沿用預演的專案，不帶 --project 會多留一個空專案
  python scripts/flow_auto.py download <專案網址> --out <資料夾>    # 補抓：資料夾裡還沒有的鏡才下載，已有的跳過

jobs.json：[{"cut": "cut04", "first": "<專案>/分鏡圖/cut04_first.png", "prompt": "...", "seconds": 4}, ...]
  要首尾幀的鏡加 "last": "<專案>/分鏡圖/cut04_last.png"；刻意只放首幀就寫 "last": null。
  沒寫 last、首幀旁邊卻有 cutNN_last.png → 送出前就停下來問（漏寫的話片尾不會停在尾幀，而且不會報錯）。
  模型一律 Omni 1.1 Flash（秒數照分鏡選 4／6／8／10）；某鏡真的要 Veo 3.1 - Lite 才寫 "model": "lite"（固定 8 秒）。

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
sys.stderr.reconfigure(encoding="utf-8")   # sys.exit 的中文訊息走 stderr，沒設在 Git Bash 會變亂碼（2026-10-31）
ROOT = Path(__file__).resolve().parents[1]
PROFILE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "flow_auto" / "chrome_profile"
FLOW = "https://flow.google.com/"
SECONDS = (4, 6, 8, 10)
OMNI, LITE = "Omni 1.1 Flash", "Veo 3.1 - Lite"
# 一律 Omni（老師 2026-10-30 定）：秒數能照分鏡選，4 秒 7／6 秒 10／8 秒 12／10 秒 15 點；
# Lite 不能選秒數、固定 8 秒 10 點，短鏡反而貴，首尾幀還得加速塞回分鏡
LITE_SECONDS = 8
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
        # --hide-crash-restore-bubble：Chrome 被強制關過之後不要每次都跳「你要還原網頁嗎？」
        args=["--disable-blink-features=AutomationControlled", "--hide-crash-restore-bubble"])
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
    return {"tile": page.locator("main").get_by_role("group").count(),
            "fail": page.get_by_text("失敗", exact=True).count()}


def choose_settings(page, seconds, model):
    # 設定面板是一組 radio（2026-10-27 inspect）；新專案預設 x 2，一定要切回 x 1，不然點數加倍。
    # 模型要先選：Veo 3.1 - Lite 的面板沒有解析度和秒數（固定 720p、8 秒，2026-10-30 inspect），換模型會換掉下面那幾排
    settings_chip(page).click()
    page.wait_for_timeout(800)
    for label in ("影片", "影格"):
        page.get_by_role("radio", name=label, exact=True).click()
        page.wait_for_timeout(300)
    model_btn = page.get_by_role("button", name="選取模型系列")
    if model not in model_btn.inner_text():
        model_btn.click()
        page.get_by_role("menuitem", name=model, exact=True).click()
        page.wait_for_timeout(1200)
    if model not in model_btn.inner_text():
        raise RuntimeError(f"模型沒切到 {model}：{model_btn.inner_text()!r}")
    labels = ("16:9", "720p", f"{seconds} 秒", "x 1") if model == OMNI else ("16:9", "x 1")
    for label in labels:
        page.get_by_role("radio", name=label, exact=True).click()
        page.wait_for_timeout(300)
    cost = page.get_by_role("link", name=re.compile(r"^\d+\s*點$")).first.inner_text()
    page.keyboard.press("Escape")
    chip = settings_chip(page).inner_text()
    want = f"{seconds if model == OMNI else LITE_SECONDS} 秒"
    if want not in chip or "x 1" not in chip.replace("x1", "x 1"):
        raise RuntimeError(f"設定沒套上：{chip!r}")
    return int(re.search(r"(\d+)", cost).group(1))


def upload_media(page, img):
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


def pick_frame(page, slot, img):
    # slot 是「開始」或「結束」，兩格開的是同一個「選取畫面圖像」視窗（2026-10-30 inspect）。
    # 點清單裡已選取的那張（剛上傳的排最上面、預設選取）會直接設好、視窗自己關；
    # 點其他張只會選取＋預覽，要再按「新增至提示詞」——首尾幀一起上傳時尾幀排最上面，首幀就是這種。
    page.get_by_role("button", name=slot, exact=True).click()
    heading = page.get_by_role("heading", name="選取畫面圖像")
    heading.wait_for(timeout=15_000)
    page.get_by_role("option", name=img.name, exact=True).first.click()
    page.wait_for_timeout(1500)
    if heading.count():
        page.get_by_role("button", name="新增至提示詞").click()
    heading.wait_for(state="detached", timeout=15_000)
    # 設好的格子會從「開始」／「結束」換成 button「圖像素材」（內含縮圖），空的那顆按鈕就不見了
    page.get_by_role("button", name=slot, exact=True).wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(1000)


def clear_frames(page):
    # 上一鏡的首尾幀會留在輸入列（預演必定、送出後可能），不清掉就找不到空的「開始」格；
    # 輸入列右上角的 ✕（aria「清除提示詞」）會連格子一起清
    if not page.get_by_role("button", name="圖像素材").count():
        return
    page.get_by_role("button", name="清除提示詞").click()
    page.get_by_role("button", name="開始", exact=True).wait_for(timeout=15_000)
    if page.get_by_role("button", name="圖像素材").count():
        raise RuntimeError("按了清除提示詞，上一鏡的首尾幀還在")
    page.wait_for_timeout(800)


def set_frames(page, first, last=None):
    clear_frames(page)
    upload_media(page, first)
    if last:
        upload_media(page, last)
    pick_frame(page, "開始", first)
    if last:
        pick_frame(page, "結束", last)
        n = page.get_by_role("button", name="圖像素材").count()
        if n != 2:
            raise RuntimeError(f"首尾幀應該有 2 格縮圖，畫面上是 {n} 格")


def wait_result(page, before, timeout=GEN_TIMEOUT):
    """送出後等：多一格「失敗」→ fail；格子變多、且畫面上沒有 100% 以外的百分比 → ok（新的一格排在最前面）。
    2026-10-30 Omni 實測：生完後「100%」會一直留在格子上，完成的格子也不是 <video>（數量 0）——
    原本「等百分比消失、等 <video> 變多」兩個條件都永遠等不到，片子 40 秒就生好卻空等 15 分鐘逾時。"""
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout:
        page.wait_for_timeout(5_000)
        fails = page.get_by_text("失敗", exact=True)
        if fails.count() > before["fail"]:
            msg = fails.first.locator("xpath=..").inner_text().replace("\n", " ")
            return "fail", None, msg[:200]
        pct = page.get_by_text(re.compile(r"^\d+%$"))
        running = [t for t in (pct.nth(i).inner_text() for i in range(pct.count())) if t != "100%"]
        if running:
            if running[0] != last:
                log(f"  生成中 {running[0]}")
                last = running[0]
            continue
        tiles = page.locator("main").get_by_role("group")
        # 送出後 14 秒左右才出現第一個百分比，那段時間新格子可能已經在、只是還沒開始跑：
        # 沒看過進度就先別算完成（真的一直沒顯示百分比，等滿 1 分鐘才放行）
        if tiles.count() > before["tile"] and (last or time.time() - t0 > 60):
            page.wait_for_timeout(3_000)   # 剛到 100% 時給它一點時間把格子換成成品
            # 每格是 group（名稱＝Flow 自動取的標題），新的排第一格
            return "ok", tiles.first, ""
    return "timeout", None, f"超過 {timeout // 60} 分鐘"


CUT_NAME = re.compile(r"^cut\d+[a-z]?$")
IMAGE_TILE = re.compile(r"\.(png|jpe?g|webp)$", re.I)   # 上傳的圖片格名稱就是檔名；影片格的縮圖是延遲載入，不能靠縮圖分辨


def rename_tile(page, tile, name):
    # ⋮ →「重新命名」→ 底下冒出 textbox「可編輯的文字」＋「完成」（2026-10-30 inspect）；
    # 專案標題也叫「可編輯的文字」，所以取最後一個
    tile.hover()
    page.wait_for_timeout(800)
    tile.get_by_role("button", name="更多選項").click()
    page.get_by_text("重新命名", exact=True).first.click()
    page.wait_for_timeout(800)
    page.get_by_role("textbox", name="可編輯的文字").last.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(name)
    page.keyboard.press("Enter")
    renamed = page.locator("main").get_by_role("group", name=name, exact=True).first
    renamed.wait_for(timeout=15_000)
    return renamed


def video_tiles(page):
    """把整個專案的格子捲過一遍，回傳影片格名稱（新的在前）。格子多時下面的要捲到才會出現。"""
    names, stale = [], 0
    while stale < 3:
        groups = page.locator("main").get_by_role("group")
        before = len(names)
        for i in range(groups.count()):
            n = groups.nth(i).get_attribute("aria-label") or ""
            if n and not IMAGE_TILE.search(n) and n not in names:
                names.append(n)
        stale = stale + 1 if len(names) == before else 0
        # 清點過的頁面直接拿來下載會 TargetClosedError 存不了檔（2026-10-30 實測，
        # 滾輪或 scroll_into_view 都一樣；單獨下載不清點就正常）→ cmd_download 每支下載前都重新載入
        if groups.count():
            groups.last.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)
    return names


def cmd_download(pw, a):
    """補抓：專案裡已生好的片子照鏡號比對 --out，已經有 cutNN_flow.mp4 的跳過，沒有的才下載。
    鏡號看格子名稱（run 生完會改名成 cutNN；網頁上自己生的也可以手動改名），
    改名失敗的再用 flow_auto_log.jsonl 記下的 Flow 標題對回去。兩邊都對不上的只列出來，不猜。"""
    out = Path(a.out)
    titles = {}
    record = out / "flow_auto_log.jsonl"
    if record.exists():
        for line in record.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("title"):
                titles[r["title"]] = r["cut"]
    ctx, page = open_browser(pw)
    page.goto(a.project)
    page.wait_for_timeout(8000)
    names = video_tiles(page)
    plan, unknown, dup = {}, [], []
    for n in names:                       # 新的在前：同一鏡生過好幾次，取最新那支
        cut = n if CUT_NAME.match(n) else titles.get(n)
        if not cut:
            unknown.append(n)
        elif cut in plan:
            dup.append(f"{cut}（{n}）")
        else:
            plan[cut] = n
    got, skip, fail = [], [], []
    for cut in sorted(plan):
        dest = out / f"{cut}_flow.mp4"
        if dest.exists():
            skip.append(cut)
            continue
        for attempt in range(1, 4):   # 下載不扣點，失敗就重載再試（滑過格子有時 ⋮ 不出現）
            if page.is_closed():      # 上一支下載時 Chrome 自己關掉了 → 重開
                try:
                    ctx.close()
                except Exception:
                    pass
                ctx, page = open_browser(pw)
            page.goto(a.project)      # 每次都從剛載入的頁面下載
            page.wait_for_timeout(8000)
            tile = page.locator("main").get_by_role("group", name=plan[cut], exact=True).first
            try:
                tile.scroll_into_view_if_needed(timeout=15_000)
                download_1080p(page, tile, dest)
                got.append(cut)
                log(f"  {cut} 已下載 {dest}")
                break
            except Exception as e:
                log(f"  {cut} 第 {attempt} 次下載失敗：{e!r:.120}")
        else:
            fail.append(cut)
            log(f"  [ERR] {cut} 試了 3 次都沒下載成功")
    try:
        ctx.close()
    except Exception:
        pass
    log(f"補抓完成：新下載 {len(got)} 支 {got}，已有跳過 {len(skip)} 支，失敗 {len(fail)} 支 {fail}")
    if dup:
        log(f"  同一鏡有多支，只抓最新的：{dup}")
    if unknown:
        # 網頁上自己生的格子，名稱常是整段提示詞（含換行），只印開頭認得出是哪格就好
        log(f"  [注意] 這 {len(unknown)} 格影片對不到鏡號，沒下載（到 Flow 裡 ⋮ → 重新命名成 cutNN 再跑一次）：")
        for n in unknown:
            short = " ".join(n.split())
            log(f"    - {short[:40]}{'…' if len(short) > 40 else ''}")


def download_1080p(page, tile, dest):
    # 滑到那一格上才會出現 ♡ 和 ⋮（按鈕在格子裡面，最後一顆是 ⋮）；⋮ →「下載」→「1080p 已提升畫質」（錄影 219 秒）
    tile.hover()
    page.wait_for_timeout(800)
    try:
        dump(page, ROOT / "_flow_inspect" / "dl_hover", dest.stem)
        tile.get_by_role("button", name="更多選項").click()
        page.get_by_text("下載", exact=True).first.hover()
        page.wait_for_timeout(800)
        # 不靠瀏覽器下載：按 1080p 後 Flow 先向 flow-content.google/<id>_upsampled?...Signature=... 要整支影片，
        # 再轉成 blob 觸發下載，而 Chrome 常在這時把分頁連瀏覽器一起關掉——save_as 與 response.body()
        # 都拿到 TargetClosedError（2026-10-30 實測，沒有當機紀錄）。所以只攔那個帶簽章的網址，
        # 由 Python 自己下載，Chrome 之後關不關都不影響。
        with page.expect_request(lambda r: "_upsampled" in r.url, timeout=10 * 60_000) as req:
            page.get_by_text("1080p", exact=True).first.click()
        url = req.value.url
    except Exception:
        if not page.is_closed():
            dump(page, ROOT / "_flow_inspect" / ("err_dl_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")), dest.stem)
        raise
    import urllib.request
    with urllib.request.urlopen(url, timeout=600) as r:
        body = r.read()
    if len(body) < 100_000 or body[4:8] != b"ftyp":
        raise RuntimeError(f"抓到的 1080p 不像 mp4（{len(body)} bytes）")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        old = dest.parent / "_old" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        old.mkdir(parents=True, exist_ok=True)
        dest.replace(old / dest.name)
    dest.write_bytes(body)
    try:
        page.wait_for_timeout(1500)   # 讓瀏覽器那份下載自己收尾，免得下一步撞上
    except Exception:
        pass                          # 檔案已經寫好；Chrome 這時關掉不算失敗，呼叫端自己重開


def cmd_run(pw, a):
    jobs = json.loads(Path(a.jobs).read_text(encoding="utf-8"))
    for j in jobs:
        if j.get("model", "omni") not in ("omni", "lite"):
            sys.exit(f"{j['cut']} model 只能寫 \"omni\" 或 \"lite\"，現在是 {j['model']!r}")
        j["model"] = LITE if j.get("model") == "lite" else OMNI
        if j["model"] == OMNI and int(j["seconds"]) not in SECONDS:
            sys.exit(f"{j['cut']} 秒數 {j['seconds']} 不在 {OMNI} 可選的 {SECONDS}")
        if j["model"] == LITE and int(j["seconds"]) > LITE_SECONDS:
            sys.exit(f"{j['cut']} 要 {j['seconds']} 秒，但 {LITE} 固定 {LITE_SECONDS} 秒；拆鏡或拿掉 \"model\": \"lite\"")
        first = Path(j["first"])
        if not first.exists():
            sys.exit(f"{j['cut']} 找不到首幀 {j['first']}")
        if "last" not in j:
            # 沒寫 last：首幀旁邊有對應的尾幀檔就停下來問，不要默默只放首幀
            guess = [first.with_name(first.name.replace("_first", "_last")),
                     first.with_name(f"{j['cut']}_last{first.suffix}")]
            found = [g for g in dict.fromkeys(guess) if g != first and g.exists()]
            if found:
                sys.exit(f"{j['cut']} 沒寫 last，但旁邊有尾幀 {found[0]}。\n"
                         f"  要首尾幀 → 補 \"last\": \"{found[0].as_posix()}\"；刻意只放首幀 → 寫 \"last\": null")
        elif j["last"] and not Path(j["last"]).exists():
            sys.exit(f"{j['cut']} 找不到尾幀 {j['last']}")
    out = Path(a.out)
    record = out / "flow_auto_log.jsonl"
    ctx, page = open_browser(pw)
    page.goto(a.project or FLOW)
    page.wait_for_timeout(5000)
    if a.project and page.get_by_text("找不到專案").count():
        # 專案已被刪掉時 Flow 只顯示這行字，不處理的話要等 30 秒才在設定按鈕那裡逾時，看不出原因
        ctx.close()
        sys.exit(f"Flow 顯示「找不到專案」：{a.project}\n  可能已被刪掉；拿掉 --project 會開新專案")
    if not a.project:
        page.get_by_text("新增專案").first.click()
        page.wait_for_timeout(6000)
    log(f"專案：{page.url}")
    for j in jobs:
        cut = j["cut"]
        last = Path(j["last"]) if j.get("last") else None
        want = int(j["seconds"])
        gen = want if j["model"] == OMNI else LITE_SECONDS
        trim = "" if gen == want else f"、分鏡 {want} 秒要剪"
        log(f"== {cut}（{j['model']}，生 {gen} 秒{trim}，{'首尾幀' if last else '只有首幀'}）")
        try:
            cost = choose_settings(page, int(j["seconds"]), j["model"])   # 先切影片模式，「開始」「結束」格才會出現
            set_frames(page, Path(j["first"]), last)
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
        rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "cut": cut, "project": page.url,
               "seconds": j["seconds"], "model": j["model"], "last": bool(last), "cost": cost, "status": status, "msg": msg}
        if status == "ok":
            rec["title"] = tile.get_attribute("aria-label")   # Flow 自取的標題；改名失敗時 download 靠它對回鏡號
            try:
                tile = rename_tile(page, tile, cut)
            except Exception as e:
                log(f"  [注意] 改名成 {cut} 失敗（{e!r:.120}），download 會用標題 {rec['title']!r} 對鏡號")
            dest = out / f"{cut}_flow.mp4"
            try:
                download_1080p(page, tile, dest)
                rec["file"] = str(dest)
                log(f"  完成，已下載 {dest}")
            except Exception as e:
                # 片子已經生好、點數已扣，下載失敗不該讓後面的鏡頭停擺；之後用 download 補抓
                rec["status"] = "ok_not_downloaded"
                log(f"  [注意] {cut} 已生成但下載失敗（{e!r:.120}），之後跑 download 補抓")
        out.mkdir(parents=True, exist_ok=True)
        with record.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if status != "ok":
            log(f"  {cut} {status}：{msg}——停下，不自動重試")
            break
    if not a.go and not a.project:
        # 正式送出不帶 --project 會再開一個新專案，預演這個就變成留在 Flow 上的空專案（2026-10-31 實際發生）
        log("正式送出請沿用這個專案，免得多留一個空專案：")
        log(f'  python scripts/flow_auto.py run "{a.jobs}" --out "{a.out}" --project {page.url} --go')
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
    p = sub.add_parser("download", help="補抓：專案裡生好、--out 還沒有的片子照鏡號下載")
    p.add_argument("project", help="Flow 專案網址（flow_auto_log.jsonl 的 project 欄有記）")
    p.add_argument("--out", required=True, help="跟 run 用同一個資料夾，才比得出哪些已經下載過")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        {"login": cmd_login, "inspect": cmd_inspect, "run": cmd_run, "download": cmd_download}[a.cmd](pw, a)


if __name__ == "__main__":
    main()
