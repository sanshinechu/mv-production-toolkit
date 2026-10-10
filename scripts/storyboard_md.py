# -*- coding: utf-8 -*-
"""讀 mv-11 產出的分鏡表（storyboard_vN.md）→ 跟 make_mv.STORYBOARD 同形狀的 list。

mv-11 規定欄位：`Cut | 時間 | 秒數 | 歌詞對應 | 畫面 | 動畫 | 進/出轉場`
回傳 [(前綴, 動畫, 進場轉場, 離場轉場, 秒數), ...]，前綴是 `cutNN` 或 `cutNN_短名`。
make_mv.py、review_mv.py、collect_videos.py 共用，三支才會用同一份分鏡（2026-10-10 影片分流）。
"""
import re
from pathlib import Path

ANIMS = {"zoom_in", "zoom_out", "pan_left", "pan_right"}
TRANS = {"fadein", "fade", "whiteflash", "fadeout"}


def _cells(line):
    return [c.strip().strip("`*") for c in line.strip().strip("|").split("|")]


def load(path):
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    head = None
    rows = []
    for ln in lines:
        if not ln.strip().startswith("|"):
            if head is not None and rows:
                break          # 表格結束（只讀第一張含「秒數」「動畫」的表）
            continue
        c = _cells(ln)
        if head is None:
            if any("秒數" in x for x in c) and any("動畫" in x for x in c) and any(x.lower().startswith("cut") for x in c):
                head = c
            continue
        if set("".join(c)) <= set("-: "):
            continue
        rows.append(dict(zip(head, c)))
    if not rows:
        raise ValueError(f"{path} 找不到 mv-11 格式的分鏡表（要有 Cut／秒數／動畫／進/出轉場 欄）")

    def col(r, key):
        return next((v for k, v in r.items() if key in k.lower() or key in k), "")

    out = []
    for r in rows:
        raw = col(r, "cut")
        m = re.search(r"(\d+)", raw)
        if not m:
            raise ValueError(f"Cut 欄看不懂：{raw!r}")
        n = int(m.group(1))
        short = re.sub(r"^\s*(?:cut)?\s*\d+[_\s-]*", "", raw, flags=re.I).strip()
        prefix = f"cut{n:02d}" + (f"_{short}" if re.fullmatch(r"[A-Za-z0-9_]+", short or "-") else "")
        dur = float(re.search(r"[\d.]+", col(r, "秒數")).group(0))
        anim = col(r, "動畫").lower()
        anim = next((a for a in ANIMS if a in anim), "zoom_in")
        tr = [t.strip().lower() for t in re.split(r"[/／、,]", col(r, "轉場"))]
        t_in = tr[0] if tr and tr[0] in TRANS else "fade"
        t_out = tr[1] if len(tr) > 1 and tr[1] in TRANS else "fade"
        out.append((prefix, anim, t_in, t_out, dur))
    return out


if __name__ == "__main__":
    import argparse
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="解析 mv-11 分鏡表，印出每鏡（前綴, 動畫, 進場, 離場, 秒數）與總長")
    ap.add_argument("storyboard", help="storyboard_vN.md")
    a = ap.parse_args()
    rows = load(a.storyboard)
    for row in rows:
        print(row)
    print(f"共 {len(rows)} 鏡，總長 {round(sum(r[4] for r in rows), 2)} 秒")
