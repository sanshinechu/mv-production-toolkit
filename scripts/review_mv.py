# -*- coding: utf-8 -*-
r"""
review_mv.py — MV 成片自動檢查（讀 make_mv.py 的 STORYBOARD）

交給人看之前先自己審一遍。數字只是警示，抽格圖和切點圖一定要人逐張看。

檢查項目：
  0 結構    分鏡秒數加總 = 成片長度 = 音樂長度（給 --music 才比）
  1 逐鏡抽格 每鏡在「淡入淡出之外」平均抽 4 格拼成總覽圖 → 看多手多腳、臉崩、亂碼字、黑邊
  2 動態    每鏡頭尾畫面差多少，太小代表 Ken Burns 沒套上（畫面整段不動）
  3 黑畫面／定格 排除轉場本來就有的黑，只回報「不該黑的地方黑了」「不該停的地方停了」
  4 響度    整體 LUFS 與真峰值（目標約 -15.5 LUFS、峰值 -1 dBFS 以下）
  5 切點    每個切點前後各抽一格並排；白閃轉場標為刻意，其餘明暗差大的列提示

用法：
  python review_mv.py <成片.mp4> --music <原曲.mp3>
  （要跟產生這支片的 make_mv.py 同一份 STORYBOARD；本檔與 make_mv.py 放同一個資料夾）

輸出：成片旁的 review\ 資料夾
  <片名>_pass1.jpg   逐鏡抽格總覽
  <片名>_cuts.jpg    切點前後對照
  <片名>_review.json 全部數字

改寫自 shanshiba-workflow 的 review.py（MIT License, mathruffian-dot），
依本專案 MV 特性改：淡入淡出與白閃是刻意的、靜圖 Ken Burns 不查雜訊、沒有台詞所以不做逐句聽寫。
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_mv  # noqa: E402  只讀 STORYBOARD、FPS、fade_durations，不會執行組裝

# 門檻（調整前先看理由）
LUFS_RANGE = (-16.5, -14.5)   # MV_WORKFLOW_GUIDE 定的目標 -15.5，上下 1
PEAK_MAX = -1.0               # 真峰值上限 dBFS；超過代表限幅沒做或爆音
DUR_TOL = 0.25                # 分鏡加總與成片、音樂長度的容許差（秒）
MOTION_MIN = 1.5              # 鏡頭頭尾畫面平均差（0-255）低於這個 = 幾乎沒動
JUMP_WARN = 12                # 切點兩側明暗差（0-255），沿用原版門檻
EDGE = 0.15                   # 判斷黑畫面／定格是否落在轉場內的容許誤差（秒）

FONT = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 20)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,duration",
                        "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout or "{}")


def grab(video, t, w=448, h=252):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (w, h), raw) if len(raw) == w * h * 3 else Image.new("RGB", (w, h))


def label(im, text, color=(255, 255, 0)):
    ImageDraw.Draw(im).text((6, 4), text, font=FONT, fill=color, stroke_width=2, stroke_fill=(0, 0, 0))


def build_shots():
    """把 STORYBOARD 換算成每鏡的起訖與「乾淨區」（扣掉淡入淡出）"""
    shots, t = [], 0.0
    for prefix, anim, t_in, t_out, dur in make_mv.STORYBOARD:
        in_d, out_d = make_mv.fade_durations(t_in, t_out)
        shots.append(dict(id=prefix.split("_")[0], name=prefix, anim=anim, t_in=t_in, t_out=t_out,
                          start=round(t, 3), dur=dur, end=round(t + dur, 3),
                          clean_a=round(t + in_d, 3), clean_b=round(t + dur - out_d, 3)))
        t += dur
    return shots


def in_transition(a, b, shots):
    """[a, b] 這段是否完全落在某個淡入或淡出區間裡（含相鄰兩鏡相接的淡出＋淡入）"""
    windows = []
    for s in shots:
        windows.append((s["start"] - EDGE, s["clean_a"] + EDGE))
        windows.append((s["clean_b"] - EDGE, s["end"] + EDGE))
    windows.sort()
    merged = []
    for lo, hi in windows:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return any(lo <= a and b <= hi for lo, hi in merged)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 同 make_mv.py：避免 --help 中文亂碼
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--music", help="原始音樂檔，用來比對歌長與分鏡加總")
    ap.add_argument("--storyboard", help="跟 make_mv.py --storyboard 同一份 storyboard_vN.md（不給就用 make_mv.py 內建的）")
    args = ap.parse_args()
    if args.storyboard:
        import storyboard_md
        make_mv.STORYBOARD = storyboard_md.load(args.storyboard)

    if not shutil.which("ffmpeg"):
        sys.exit("[ERR] ffmpeg 不在 PATH")
    video = Path(args.video).resolve()
    if not video.exists():
        sys.exit(f"[ERR] 找不到成片：{video}")
    rv = video.parent / "review"
    rv.mkdir(exist_ok=True)
    stem = video.stem
    shots = build_shots()
    out, warns = {"video": str(video), "shots": len(shots)}, []

    # ---- 0 結構：秒數對不對得上
    info = probe(video)
    v_dur = float(info.get("format", {}).get("duration", 0))
    a_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    sb_total = round(sum(s["dur"] for s in shots), 2)
    out["pass0"] = dict(storyboard_total=sb_total, video_duration=round(v_dur, 2), has_audio=bool(a_streams))
    if abs(v_dur - sb_total) > DUR_TOL:
        warns.append(f"結構：成片 {v_dur:.2f}s 跟分鏡加總 {sb_total}s 差 {v_dur - sb_total:+.2f}s"
                     "（音樂比分鏡短時 -shortest 會把片尾切掉）")
    if not a_streams:
        warns.append("結構：成片沒有音軌")
    if args.music:
        m_dur = float(probe(args.music).get("format", {}).get("duration", 0))
        out["pass0"]["music_duration"] = round(m_dur, 2)
        if abs(m_dur - sb_total) > DUR_TOL:
            warns.append(f"結構：音樂 {m_dur:.2f}s 跟分鏡加總 {sb_total}s 差 {m_dur - sb_total:+.2f}s"
                         "（MV_11 規定分鏡加總要等於歌長）")

    # ---- 1 逐鏡抽格：只抽乾淨區，不然會抽到半黑的淡化格
    rows = []
    for s in shots:
        a, b = s["clean_a"], s["clean_b"]
        row = Image.new("RGB", (448 * 4, 252))
        for j in range(4):
            row.paste(grab(video, a + (b - a) * (j + 0.5) / 4), (448 * j, 0))
        label(row, f"{s['id']}  {s['start']:.1f}-{s['end']:.1f}s  {s['anim']}  {s['name']}")
        rows.append(row)
    sheet = Image.new("RGB", (448 * 4, 252 * len(rows)))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 252 * i))
    sheet.save(rv / f"{stem}_pass1.jpg", quality=82)
    out["pass1_sheet"] = f"{stem}_pass1.jpg"

    # ---- 2 動態：乾淨區頭尾兩格差太小 = 畫面沒動
    motion = []
    for s in shots:
        fa = np.asarray(grab(video, s["clean_a"] + 0.05, 320, 180), np.float32)
        fb = np.asarray(grab(video, s["clean_b"] - 0.05, 320, 180), np.float32)
        d = float(np.abs(fa - fb).mean())
        motion.append(dict(shot=s["id"], diff=round(d, 2)))
        if d < MOTION_MIN:
            warns.append(f"動態：{s['id']} 頭尾畫面幾乎一樣（差 {d:.2f}），Ken Burns 可能沒套上，或素材太單調看不出移動")
    out["pass2_motion"] = motion

    # ---- 3 黑畫面／定格 ＋ 4 響度：一次跑完
    p = subprocess.run(["ffmpeg", "-i", str(video), "-vf", "blackdetect=d=0.1:pix_th=0.10,freezedetect=n=0.001:d=0.8",
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    err = p.stderr
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    fz_s = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]
    fz_e = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)] + [v_dur] * (len(fz_s) - len(re.findall(r"freeze_end", err)))
    freezes = list(zip(fz_s, fz_e))
    bad_black = [(round(a, 2), round(b, 2)) for a, b in blacks if not in_transition(a, b, shots)]
    bad_freeze = [(round(a, 2), round(b, 2)) for a, b in freezes if not in_transition(a, b, shots)]
    out["pass3"] = dict(black_all=len(blacks), black_unexpected=bad_black, freeze_all=len(freezes), freeze_unexpected=bad_freeze)
    for a, b in bad_black:
        warns.append(f"黑畫面：{a:.2f}-{b:.2f}s 不在轉場範圍內")
    for a, b in bad_freeze:
        warns.append(f"定格：{a:.2f}-{b:.2f}s 畫面停住超過 0.8 秒，而且不是轉場")

    summ = err[err.rfind("Summary:"):]
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", summ)
    pk = re.search(r"Peak:\s*(-?[\d.]+) dBFS", summ)
    lufs = float(m.group(1)) if m else None
    peak = float(pk.group(1)) if pk else None
    out["pass4"] = dict(lufs=lufs, true_peak_dbfs=peak, target=f"{LUFS_RANGE[0]}~{LUFS_RANGE[1]} LUFS, peak <= {PEAK_MAX}")
    if a_streams and lufs is not None:
        if not LUFS_RANGE[0] <= lufs <= LUFS_RANGE[1]:
            warns.append(f"響度：{lufs} LUFS，目標 {LUFS_RANGE[0]}~{LUFS_RANGE[1]}（照 MV_WORKFLOW_GUIDE 的兩段式調）")
        if peak is not None and peak > PEAK_MAX:
            warns.append(f"響度：真峰值 {peak} dBFS 超過 {PEAK_MAX}，可能爆音（限幅要加 level=false）")

    # ---- 5 切點：前一鏡乾淨區最後一格 vs 下一鏡乾淨區第一格
    tiles, cuts = [], []
    for a, b in zip(shots, shots[1:]):
        L = grab(video, a["clean_b"] - 0.05, 320, 180)
        R = grab(video, b["clean_a"] + 0.05, 320, 180)
        dl = float(np.abs(np.asarray(L, np.float32).mean(axis=(0, 1)) - np.asarray(R, np.float32).mean(axis=(0, 1))).mean())
        flash = "whiteflash" in (a["t_out"], b["t_in"])
        cuts.append(dict(cut=f"{a['id']}|{b['id']}", at=b["start"], brightness_diff=round(dl, 1), whiteflash=flash))
        row = Image.new("RGB", (640, 180))
        row.paste(L, (0, 0))
        row.paste(R, (320, 0))
        tag = "白閃（刻意）" if flash else f"明暗差 {dl:.0f}"
        label(row, f"{a['id']}|{b['id']} {b['start']:.1f}s {tag}", (255, 80, 80) if (dl > JUMP_WARN and not flash) else (255, 255, 0))
        tiles.append(row)
    if tiles:
        sheet = Image.new("RGB", (640 * 4, 180 * ((len(tiles) + 3) // 4)))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % 4) * 640, (i // 4) * 180))
        sheet.save(rv / f"{stem}_cuts.jpg", quality=82)
    out["pass5_cuts"] = cuts
    out["pass5_sheet"] = f"{stem}_cuts.jpg"
    jumps = [c["cut"] for c in cuts if c["brightness_diff"] > JUMP_WARN and not c["whiteflash"]]

    out["warnings"] = warns
    out["hints"] = [f"切點明暗差較大（經過淡入淡出，通常不刺眼，看切點圖確認氣氛有沒有斷掉）：{', '.join(jumps)}"] if jumps else []
    out["not_checked"] = ["切點是否對拍（第二版）", "歌詞字幕對不對（第二版）", "字幕區淨空（make_mv 目前不燒字幕）",
                          "多手多腳、臉崩、亂碼字、黑邊 → 只能人看 pass1 圖"]
    (rv / f"{stem}_review.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n== MV 自動檢查：{video.name} ==")
    print(f"  {len(shots)} 鏡，分鏡 {sb_total}s，成片 {v_dur:.2f}s，響度 {lufs} LUFS／峰值 {peak} dBFS")
    print(f"  轉場黑畫面 {len(blacks) - len(bad_black)} 段（刻意，已排除）")
    if warns:
        print(f"\n  ⚠️ 要處理（{len(warns)}）：")
        for w in warns:
            print(f"   - {w}")
    else:
        print("\n  ✅ 自動檢查沒有發現問題")
    for h in out["hints"]:
        print(f"\n  💡 {h}")
    print(f"\n  👀 一定要人看：{rv / out['pass1_sheet']}")
    print(f"               {rv / out['pass5_sheet']}")
    print(f"  📄 數字：{rv / (stem + '_review.json')}")
    print("  ⏸️ 沒檢查：" + "、".join(out["not_checked"][:3]))


if __name__ == "__main__":
    main()
