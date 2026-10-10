# -*- coding: utf-8 -*-
r"""影片分流的收件與交件前檢查（規則見 docs/影片分流策略.md）。

用法：
  python scripts/collect_videos.py <MV名> --storyboard outputs/<MV名>/storyboard_v2.md            # 🅰 Colab：搬回＋檢查
  python scripts/collect_videos.py <MV名> --storyboard outputs/<MV名>/storyboard_v2.md --check    # 🅱 Flow 放好後：只檢查

- 搬回：colab_mv/outputs/<MV名>/cutNN/clip_1080p.mp4 → outputs/<MV名>/videos-raw/cutNN_<短名>.mp4
  （同編號已有舊檔就先移到 videos-raw/_old/<時間>/，不刪）
- 檢查：分鏡表每一鏡都要有「剛好一支」cutNN*.mp4、秒數 ≥ 分鏡秒數、1920×1080、24 fps；多出來的檔只警告
  （make_mv.py 組裝時會再對實際採用的影片擋一次解析度與 fps，不靠「記得先跑 --check」）
- colab_mv 位置從專案根目錄的 colab_mv.lnk 解析（各機碟號不同，不寫死；Drive 共用捷徑在本機是 .lnk）
有錯誤 exit 1。
"""
import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import storyboard_md  # noqa: E402

W, H = 1920, 1080


def colab_dir():
    lnk = ROOT / "colab_mv.lnk"
    if (ROOT / "colab_mv").is_dir():
        return ROOT / "colab_mv"
    if not lnk.exists():
        sys.exit(f"找不到 {lnk}（colab_mv 共用資料夾的捷徑）")
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}').TargetPath"],
                       capture_output=True, text=True, encoding="utf-8")
    p = Path(r.stdout.strip())
    if not p.is_dir():
        sys.exit(f"colab_mv.lnk 解析不出資料夾：{r.stdout.strip()!r} {r.stderr.strip()[:200]}")
    return p


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    num, _, den = s.get("r_frame_rate", "0/1").partition("/")
    return (s.get("width"), s.get("height"), float(j.get("format", {}).get("duration", 0)),
            round(float(num) / float(den or 1), 2))


def collect(mv, sb, raw):
    src_root = colab_dir() / "outputs" / mv
    if not src_root.is_dir():
        sys.exit(f"Colab 端沒有 {src_root}")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    n = 0
    for prefix, *_ in sb:
        num = prefix.split("_")[0]
        src = src_root / num / "clip_1080p.mp4"
        if not src.exists():
            print(f"  · {num}：Colab 端還沒有 clip_1080p.mp4")
            continue
        olds = [p for p in raw.glob(f"{num}*.mp4") if re.match(rf"{num}(\D|$)", p.stem)]
        for o in olds:
            (raw / "_old" / stamp).mkdir(parents=True, exist_ok=True)
            shutil.move(str(o), str(raw / "_old" / stamp / o.name))
        shutil.copy2(src, raw / f"{prefix}.mp4")
        n += 1
        print(f"  ← {num}：{src.relative_to(src_root.parent)} → videos-raw/{prefix}.mp4" + (f"（舊檔移到 _old/{stamp}）" if olds else ""))
    print(f"搬回 {n} 鏡")


def check(sb, raw):
    errs, warns = [], []
    want = set()
    for prefix, _a, _i, _o, dur in sb:
        num = prefix.split("_")[0]
        want.add(num)
        m = [p for p in raw.glob(f"{num}*.mp4") if re.match(rf"{num}(\D|$)", p.stem)]
        if not m:
            errs.append(f"{num}：缺影片（分鏡 {dur}s）")
            continue
        if len(m) > 1:
            errs.append(f"{num}：有 {len(m)} 支（{', '.join(p.name for p in m)}），只能留一支")
            continue
        w, h, d, fps = probe(m[0])
        line = f"{m[0].name}：{w}×{h}、{d:.2f}s、{fps} fps（分鏡 {dur}s）"
        if (w, h) != (W, H):
            errs.append(f"{line} → 不是 {W}×{H}")
        elif d + 0.05 < dur:
            errs.append(f"{line} → 秒數不夠")
        elif abs(fps - 24) > 0.1:
            errs.append(f"{line} → 不是 24 fps（make_mv.py 也會擋；確定要用得加 --allow-fps）")
        else:
            print(f"  ✓ {line}")
    for p in raw.glob("*.mp4"):
        mm = re.match(r"(cut\d+)", p.stem)
        if not mm or mm.group(1) not in want:
            warns.append(f"{p.name} 對不上分鏡表的任何一鏡（檔名要 cutNN_短名.mp4）")
    for x in warns:
        print("  ⚠️", x)
    for x in errs:
        print("  ❌", x)
    print(f"檢查：{len(sb)} 鏡，錯誤 {len(errs)}、警告 {len(warns)}")
    return not errs


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("mv", help="MV 名稱＝outputs/ 與 colab_mv/outputs/ 底下的資料夾名")
    ap.add_argument("--storyboard", required=True, help="mv-11 的 storyboard_vN.md")
    ap.add_argument("--check", action="store_true", help="只檢查（Flow 路線用），不從 Colab 搬")
    a = ap.parse_args()
    sb = storyboard_md.load_or_exit(a.storyboard)
    raw = ROOT / "outputs" / a.mv / "videos-raw"
    raw.mkdir(parents=True, exist_ok=True)
    if not a.check:
        collect(a.mv, sb, raw)
    sys.exit(0 if check(sb, raw) else 1)


if __name__ == "__main__":
    main()
