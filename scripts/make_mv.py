# -*- coding: utf-8 -*-
r"""
make_mv.py — 純 ffmpeg 組裝 MV（《那些年，還在》12 cut 版）

流程：
1. 每張圖用 ffmpeg zoompan 做 Ken Burns 動畫 + fade in/out
2. concat 串接 12 段短片
3. 音樂裁到分鏡總長、fade out 結尾、兩段式響度到 -15.5 LUFS（2026-10-09 加）
4. 輸出 1280x720 MP4
5. 做完跑 review_mv.py 自動檢查（抽格、動態、黑畫面、響度、切點）

用法（每支 MV 改上面的 STORYBOARD，或複製本檔到該片資料夾再改）：
  python make_mv.py --shots <分鏡圖資料夾> --music <歌曲.mp3> --out <輸出.mp4>
  例：python make_mv.py --shots "..\..\11_Opencode影片工作流\mv_project\shots" ^
        --music "..\..\11_Opencode影片工作流\mv_project\music\那些年，還在.mp3" ^
        --out "..\..\11_Opencode影片工作流\mv_project\final\MV_那些年還在.mp4"

2026-10-09 從 11_Opencode影片工作流/tools/ 搬來入庫（舊檔留在該處 tools/_old/）。
不用 -shortest（AGENTS.md 規定，會截斷音樂）：音樂先檢查夠長，再明確用 -t 裁到分鏡總長。
"""
import argparse
import re
import subprocess
import sys
import shutil
from pathlib import Path

# === 分鏡表（v2.1：切點對齊 word-level 歌詞時間碼與能量曲線）===
# (檔名前綴, 動畫類型, 進場轉場, 離場轉場, 秒數)
STORYBOARD = [
    ("cut01_playground_sunset",      "zoom_in",   "fadein",    "fade",       4.4),
    ("cut02_trees_flag_wind",        "pan_right", "fade",      "fade",       5.3),
    ("cut03_blackboard_warm",        "zoom_in",   "fade",      "fade",       5.1),
    ("cut04_classroom_backview",     "pan_left",  "fade",      "fade",       5.5),
    ("cut05_corridor_run_backlit",   "zoom_in",   "fade",      "whiteflash", 7.7),
    ("cut06_courtyard_circle",       "zoom_out",  "whiteflash","fade",       7.6),
    ("cut07_paper_plane_sky",        "pan_right", "fade",      "fade",       5.7),
    ("cut08_rain_playground_run",    "zoom_in",   "fade",      "fade",       5.6),
    ("cut09_rain_window_drops",      "zoom_in",   "fade",      "fade",       5.4),
    ("cut10_graduation_throw",       "zoom_out",  "fade",      "whiteflash", 5.7),
    ("cut11_old_photo_desk",         "zoom_in",   "whiteflash","fade",       5.3),
    ("cut12_empty_classroom_sunset", "zoom_out",  "fade",      "fadeout",    8.7),
]
WIDTH, HEIGHT = 1280, 720
FPS = 24
INTENSITY = 0.12        # Ken Burns 強度
TARGET_LUFS = -15.5     # 成片響度（MV_WORKFLOW_GUIDE；YouTube 標準 -14，留一點餘裕）

def find_ffmpeg():
    f = shutil.which("ffmpeg")
    return Path(f) if f else None

def find_image(shots_dir, prefix):
    # 找 shots 目錄裡符合前綴的 png（draw-free 輸出檔名帶時間戳）
    matches = list(shots_dir.glob(f"{prefix}_*.png"))
    if not matches:
        matches = list(shots_dir.glob(f"{prefix}*.*"))
    if not matches:
        # 場景命名不同版本時，退回只比對 cut 編號（如 v3 塗鴉版 cut01_desk_*）
        matches = list(shots_dir.glob(f"{prefix.split('_')[0]}_*.png"))
    return matches[0] if matches else None

def build_zoompan(anim, frames, w, h):
    pad = 1.0 + INTENSITY
    bw = int(w * pad)
    bh = int(h * pad)
    if anim == "zoom_in":
        return (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,"
                f"crop={bw}:{bh},"
                f"zoompan=z='1.0+({pad-1.0})*on/{frames}':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={w}x{h}:fps={FPS}")
    if anim == "zoom_out":
        return (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,"
                f"crop={bw}:{bh},"
                f"zoompan=z='{pad}-({pad-1.0})*on/{frames}':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={w}x{h}:fps={FPS}")
    # 平移：固定放大 pad 倍，畫面在多出來的 12% 寬度裡從一端移到另一端。
    # 2026-10-09 修：原本 z='1.0'，可移動範圍 iw-iw/zoom = 0，平移鏡完全不會動（review_mv.py 抓到）。
    # 素材先放大到輸出的 2 倍再平移，每格移動量才不會被捨入成整數像素而一頓一頓。
    pw, ph = w * 2, h * 2
    if anim == "pan_left":
        return (f"scale={pw}:{ph}:force_original_aspect_ratio=increase,"
                f"crop={pw}:{ph},"
                f"zoompan=z='{pad}':"
                f"x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={w}x{h}:fps={FPS}")
    if anim == "pan_right":
        return (f"scale={pw}:{ph}:force_original_aspect_ratio=increase,"
                f"crop={pw}:{ph},"
                f"zoompan=z='{pad}':"
                f"x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={w}x{h}:fps={FPS}")
    return f"scale={w}:{h}"

def fade_durations(trans_in, trans_out):
    """進場、離場淡化各幾秒（review_mv.py 也讀這裡，用來分辨故意的黑畫面）"""
    in_d = 1.0 if trans_in == "fadein" else 0.5 if trans_in == "fade" else 0.4
    out_d = 1.5 if trans_out == "fadeout" else 0.5
    return in_d, out_d

def build_fade_filter(trans_in, trans_out, dur, fps):
    """回傳 fade 濾鏡字串（加在 zoompan 後面）"""
    parts = []
    in_d, out_d = fade_durations(trans_in, trans_out)
    parts.append(f"fade=t=in:st=0:d={in_d}")
    parts.append(f"fade=t=out:st={dur-out_d}:d={out_d}")
    if trans_in == "whiteflash":
        # 白閃：先淡入到白，再從白淡入到畫面（用 fade 疊代）
        parts.append(f"fade=t=in:st=0:d=0.3:color=white")
    if trans_out == "whiteflash":
        parts.append(f"fade=t=out:st={dur-0.4}:d=0.4:color=white")
    return ",".join(parts)

def make_clip(ffmpeg, img_path, anim, trans_in, trans_out, dur, out_path, tmp_dir):
    frames = int(dur * FPS)
    vf = build_zoompan(anim, frames, WIDTH, HEIGHT)
    fade = build_fade_filter(trans_in, trans_out, dur, FPS)
    full_vf = f"{vf},{fade}"

    cmd = [
        str(ffmpeg), "-y",
        "-loop", "1", "-i", str(img_path),
        "-vf", full_vf,
        "-t", str(dur),
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] {r.stderr[-400:]}")
        return False
    return True

def find_video(videos_dir, prefix):
    """videos-raw/ 裡同 cut 編號的影片（影片分流兩條路的成品都放這，檔名 cutNN_*.mp4）。_old/ 不算。"""
    if not videos_dir:
        return None
    num = prefix.split("_")[0]
    m = sorted(p for p in videos_dir.glob(f"{num}*.mp4") if re.match(rf"{num}(\D|$)", p.stem))
    if len(m) > 1:
        print(f"  [ERR] {num} 有 {len(m)} 支影片，留一支、其餘移到 _old/：{[p.name for p in m]}"); sys.exit(1)
    return m[0] if m else None

def make_video_clip(ffmpeg, video, trans_in, trans_out, dur, out_path):
    """影片素材：裁到分鏡秒數、縮放裁切到輸出尺寸、丟掉原聲（H3／Veo 自己配的聲音不要）、套同一套淡入淡出。"""
    have = probe_duration(video)
    if have + 0.05 < dur:
        print(f"  [ERR] {video.name} 只有 {have:.2f}s，分鏡要 {dur}s（先跑 collect_videos.py --check）"); return False
    # 2026-10-10 檢視意見：「先 --check 再組裝」只是約定，這裡自己擋——低於輸出解析度的影片會被硬放大混進成片
    w, h, fps = probe_video(video)
    if (w < WIDTH or h < HEIGHT) and not ALLOW_LOWRES:
        print(f"  [ERR] {video.name} 是 {w}×{h}，低於輸出 {WIDTH}×{HEIGHT}（Colab 要先跑 upscale.py；"
              "真的要硬放大才加 --allow-lowres）"); return False
    if abs(fps - FPS) > 0.1 and not ALLOW_FPS:
        print(f"  [ERR] {video.name} 是 {fps} fps，不是 {FPS}（轉換會掉格或重複格；確定要用才加 --allow-fps）"); return False
    vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
          f"fps={FPS},setsar=1,{build_fade_filter(trans_in, trans_out, dur, FPS)}")
    r = subprocess.run([str(ffmpeg), "-y", "-i", str(video), "-t", str(dur), "-an", "-vf", vf,
                        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "18", str(out_path)],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] {r.stderr[-400:]}")
        return False
    return True

ALLOW_LOWRES = False
ALLOW_FPS = False

def probe_video(path):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        w, h, rate = r.stdout.strip().split(",")[:3]
        num, _, den = rate.partition("/")
        return int(w), int(h), round(float(num) / float(den or 1), 2)
    except ValueError:
        print(f"[ERR] 讀不到影片規格：{path}"); sys.exit(1)

def probe_duration(path):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        print(f"[ERR] 讀不到長度：{path}"); sys.exit(1)

def run_ff(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] {r.stderr[-600:]}"); sys.exit(1)
    return r

def normalize_audio(ffmpeg, music, total_dur, tmp_dir):
    """音樂裁到分鏡總長、結尾 2 秒淡出，再兩段式拉到 TARGET_LUFS。回傳 final.wav。

    兩段式：loudnorm 先粗調 → ebur128 量實際值 → 補差額 → 限幅。
    alimiter 一定要 level=false：預設 level=true 會把輸出自動拉到 0 dBFS（爆音邊緣），而且不會報錯。
    """
    ln = tmp_dir / "ln.wav"
    final = tmp_dir / "final.wav"
    run_ff([str(ffmpeg), "-y", "-i", str(music), "-t", f"{total_dur:.3f}",
            "-af", f"afade=t=out:st={total_dur - 2.0:.2f}:d=2.0,"
                   f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11",
            "-ar", "48000", str(ln)])
    r = run_ff([str(ffmpeg), "-i", str(ln), "-af", "ebur128", "-f", "null", "-"])
    summ = r.stderr[r.stderr.rfind("Summary:"):]
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", summ)
    measured = float(m.group(1)) if m else TARGET_LUFS
    gain = TARGET_LUFS - measured
    run_ff([str(ffmpeg), "-y", "-i", str(ln),
            "-af", f"volume={gain:.2f}dB,alimiter=limit=0.72:level=false",
            "-ar", "48000", str(final)])
    print(f"       loudnorm 後 {measured} LUFS，補 {gain:+.2f} dB，限幅 -2.9 dBFS")
    return final

def main():
    global STORYBOARD, WIDTH, HEIGHT, ALLOW_LOWRES, ALLOW_FPS
    # 2026-10-10：Windows 主控台／被別的程式（Codex 等）擷取輸出時預設 cp950，--help 的中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--shots", help="分鏡圖資料夾（Ken Burns 用；全部鏡頭都有影片時可省略）")
    p.add_argument("--videos", help="影片素材資料夾 videos-raw/（影片分流兩條路的成品，cutNN_*.mp4）")
    p.add_argument("--storyboard", help="mv-11 的 storyboard_vN.md；不給就用本檔上方的 STORYBOARD")
    p.add_argument("--size", default=f"{WIDTH}x{HEIGHT}", help="輸出尺寸，成品 1080p 用 1920x1080（預設 1280x720）")
    p.add_argument("--allow-lowres", action="store_true", help="允許低於輸出解析度的影片（會被硬放大，畫質差）")
    p.add_argument("--allow-fps", action="store_true", help=f"允許不是 {FPS} fps 的影片")
    p.add_argument("--music", required=True)
    p.add_argument("--out",   required=True)
    args = p.parse_args()
    ALLOW_LOWRES, ALLOW_FPS = args.allow_lowres, args.allow_fps
    if args.storyboard:
        import storyboard_md
        STORYBOARD = storyboard_md.load(args.storyboard)
    WIDTH, HEIGHT = map(int, args.size.lower().split("x"))
    if not args.shots and not args.videos:
        p.error("--shots 和 --videos 至少要給一個")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("[ERR] ffmpeg 不在 PATH"); sys.exit(1)
    print(f"  ffmpeg: {ffmpeg}")

    shots = Path(args.shots).resolve() if args.shots else None
    videos = Path(args.videos).resolve() if args.videos else None
    music = Path(args.music).resolve()
    out_path = Path(args.out).resolve()   # 絕對路徑：concat 清單裡的相對路徑會以清單檔所在處為準
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / "tmp_kb"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(exist_ok=True)

    total_dur = sum(s[4] for s in STORYBOARD)
    music_dur = probe_duration(music)
    if music_dur + 0.05 < total_dur:
        print(f"[ERR] 音樂 {music_dur:.2f}s 比分鏡總長 {total_dur:.2f}s 短，片尾會沒聲音。"
              "先改 STORYBOARD 秒數讓加總等於歌長（MV_11 規定）")
        sys.exit(1)
    if music_dur - total_dur > 0.25:
        print(f"  [注意] 音樂 {music_dur:.2f}s 比分鏡總長 {total_dur:.2f}s 長，"
              f"會在 {total_dur:.2f}s 淡出結束，歌的最後 {music_dur - total_dur:.1f}s 不會出現")
    print(f"\n== 開始組裝 MV ==")
    print(f"  素材：{shots}")
    print(f"  音樂：{music.name}")
    print(f"  cut 數：{len(STORYBOARD)}，總長：{total_dur}s")
    print(f"  解析度：{WIDTH}x{HEIGHT}  FPS：{FPS}")

    # Step 1: 12 個 cut
    print(f"\n  Step 1: 每鏡做成短片（有影片用影片，沒有才用圖做 Ken Burns）...")
    clip_paths = []
    for i, (prefix, anim, t_in, t_out, dur) in enumerate(STORYBOARD):
        clip = tmp / f"clip_{i:02d}.mp4"
        vid = find_video(videos, prefix)
        if vid:
            print(f"  [{i+1:02d}/{len(STORYBOARD)}] {prefix} -> 影片 {vid.name} ({t_in}/{t_out}) {dur}s")
            ok = make_video_clip(ffmpeg, vid, t_in, t_out, dur, clip)
        else:
            img = find_image(shots, prefix) if shots else None
            if not img:
                print(f"  [ERR] 找不到素材：{prefix}（videos-raw 沒影片、分鏡圖也沒有）"); sys.exit(1)
            print(f"  [{i+1:02d}/{len(STORYBOARD)}] {prefix} -> 圖 {anim} ({t_in}/{t_out}) {dur}s")
            ok = make_clip(ffmpeg, img, anim, t_in, t_out, dur, clip, tmp)
        if not ok:
            sys.exit(1)
        clip_paths.append(clip)

    # Step 2: concat 列表
    print(f"\n  Step 2: 串接 + 加音樂...")
    list_file = tmp / "concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write(f"file '{c.as_posix()}'\n")

    # Step 3: 音樂裁到分鏡長度、結尾淡出、兩段式響度
    print(f"\n  Step 3: 音樂響度標準化（目標 {TARGET_LUFS} LUFS）...")
    final_wav = normalize_audio(ffmpeg, music, total_dur, tmp)

    # Step 4: 組合最終 MP4
    cmd = [
        str(ffmpeg), "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(final_wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_dur:.3f}",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] {r.stderr[-600:]}"); sys.exit(1)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n  [OK] {out_path}")
    print(f"       大小：{size_mb:.1f} MB")

    # 驗證時長
    probe = subprocess.run(
        [shutil.which("ffprobe") or "ffprobe",
         "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(out_path)],
        capture_output=True, text=True)
    print(f"       時長：{probe.stdout.strip()} 秒")

    print(f"\n  清理暫存...")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n== 完成 ==")

if __name__ == "__main__":
    main()