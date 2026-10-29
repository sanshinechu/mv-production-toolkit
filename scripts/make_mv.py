# -*- coding: utf-8 -*-
r"""
make_mv.py — 純 ffmpeg 組裝 MV（《那些年，還在》12 cut 版）

流程：
1. 每張圖用 ffmpeg zoompan 做 Ken Burns 動畫 + fade in/out
2. concat 串接 12 段短片
3. 音樂裁到分鏡總長、fade out 結尾、兩段式響度到 -15.5 LUFS（2026-10-09 加）
4. 輸出 1280x720 MP4
5. 做完跑 review_mv.py 自動檢查（抽格、動態、黑畫面、響度、切點）

微電影（mv-13／mv-14，2026-10-17）：--audio-cues 讀片頭／片尾戲秒數、口白（音樂平滑閃避）與環境音；
--sub-lyrics／--sub-dialog 燒雙層字幕，歌詞自動平移片頭秒數並拿掉跟口白重疊的條目。
--cover <封面.png>（2026-10-27）：字幕燒完後在最前面接封面（預設 3 秒、靜音）；review_mv.py 要給同樣的 --cover-sec。

用法（每支 MV 改上面的 STORYBOARD，或複製本檔到該片資料夾再改）：
  python make_mv.py --shots <分鏡圖資料夾> --music <歌曲.mp3> --out <輸出.mp4>
  例：python make_mv.py --shots "outputs\<MV名>\shots" ^
        --music "outputs\<MV名>\<歌名>.mp3" ^
        --out "outputs\<MV名>\<MV名>_完整MV.mp4"

2026-10-09 從 11_Opencode影片工作流/tools/ 搬來入庫；11 那個資料夾 2026-10-18 起不再使用（老師決定移除）。
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
    # 分鏡可短於預設淡出時間；不夾住會產生負的 fade 起點，FFmpeg 直接失敗。
    in_d = min(in_d, dur)
    out_d = min(out_d, dur)
    parts.append(f"fade=t=in:st=0:d={in_d}")
    parts.append(f"fade=t=out:st={dur-out_d}:d={out_d}")
    if trans_in == "whiteflash":
        # 白閃：先淡入到白，再從白淡入到畫面（用 fade 疊代）
        parts.append(f"fade=t=in:st=0:d={min(0.3, dur)}:color=white")
    if trans_out == "whiteflash":
        flash_d = min(0.4, dur)
        parts.append(f"fade=t=out:st={dur-flash_d}:d={flash_d}:color=white")
    return ",".join(parts)

def make_clip(ffmpeg, img_path, anim, trans_in, trans_out, dur, out_path, tmp_dir):
    frames = int(dur * FPS)
    vf = build_zoompan(anim, frames, WIDTH, HEIGHT)
    fade = build_fade_filter(trans_in, trans_out, dur, FPS)
    full_vf = f"{vf},{fade}"

    cmd = [
        str(ffmpeg), "-nostdin", "-loglevel", "error", "-y",
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

def has_last_frame(shots_dir, prefix, fit_cuts):
    """這鏡是不是首尾幀：--fit 有列，或分鏡圖資料夾有 cutNN_last.*。"""
    num = prefix.split("_")[0]
    if num in fit_cuts:
        return True
    return bool(shots_dir and any(shots_dir.glob(f"{num}_last.*")))

def make_video_clip(ffmpeg, video, trans_in, trans_out, dur, out_path, fit=False):
    """影片素材：裁到分鏡秒數、縮放裁切到輸出尺寸、丟掉原聲（H3／Veo 自己配的聲音不要）、套同一套淡入淡出。
    fit=True（首尾幀鏡頭）且影片比分鏡長 → 整支加速塞進分鏡秒數，不剪後半：尾幀在片子最後，
    從頭剪會把它剪掉而且不報錯（Veo 3.1 Lite 在 Flow 固定生 8 秒，分鏡 4 秒就只剩前半，2026-10-30 老師定）。"""
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
    speed = ""
    if fit and have > dur + 0.05:
        ratio = have / dur
        print(f"      首尾幀：{have:.2f}s 加速 {ratio:.2f} 倍塞進 {dur}s（不剪後半）"
              + ("  [注意] 超過 2 倍，動作會明顯變快，抽幀時看一下" if ratio > 2 else ""))
        speed = f"setpts=PTS*{dur / have:.6f},"   # 放在 fps 前面，加速後再重取 24 格
    vf = (f"{speed}scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
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

DUCK_ATTACK = 0.3   # 口白開始前幾秒開始壓音樂
DUCK_RELEASE = 0.6  # 口白結束後幾秒推回（mv-14 規範）
TIMELINE_TOLERANCE = 0.05
# 對白字幕可比口白早一點出現、晚一點消失（觀眾要讀字的時間）。
# 歌詞避讓已經把對白字幕自己的區間算進去，所以這裡放寬不會造成雙字幕（2026-10-17）。
DIALOG_LEAD = 0.2   # 字幕最多比口白早出現幾秒
DIALOG_TAIL = 1.0   # 字幕最多比口白晚消失幾秒


def resolve_cue_path(p, base_dir):
    """audio_cues.json 裡的相對路徑以 json 所在資料夾為準，不看從哪裡執行（2026-10-17）。"""
    path = Path(p)
    return path if path.is_absolute() else (base_dir / path).resolve()


def load_cues(cues_path):
    """讀 audio_cues.json，把路徑解析成絕對、量好每段長度。檔案不存在直接停：
    以前只印 WARN 繼續跑，口白會安靜從成品消失。"""
    import json
    data = json.loads(cues_path.read_text(encoding="utf-8-sig"))
    base = cues_path.parent
    missing = []
    for kind in ("vo", "sfx"):
        for item in data.get(kind, []):
            item["path"] = resolve_cue_path(item["file"], base)
            if not item["path"].exists():
                missing.append(str(item["path"]))
                continue
            have = probe_duration(item["path"])
            item["dur"] = min(have, float(item["duration"])) if item.get("duration") else have
    if missing:
        print("[ERR] audio_cues.json 指到的檔案不存在（相對路徑以 json 所在資料夾為準）：")
        for m in missing:
            print(f"      {m}")
        sys.exit(1)
    return data


def vo_intervals(cues_data):
    """口白在成片時間軸上的區間 [(start, end, text)]"""
    return [(float(v.get("start", 0.0)), float(v.get("start", 0.0)) + v["dur"], v.get("text", ""))
            for v in cues_data.get("vo", [])]


def validate_mix_timeline(cues_data, total_dur, prologue_sec, epilogue_sec):
    """在送進 ffmpeg 前擋掉會被 -t 靜默裁掉的微電影時間軸設定。"""
    errors = []
    if prologue_sec < 0:
        errors.append(f"片頭戲不可為負數：{prologue_sec:.3f}s")
    if epilogue_sec < 0:
        errors.append(f"片尾戲不可為負數：{epilogue_sec:.3f}s")
    song_window = total_dur - prologue_sec - epilogue_sec
    if song_window < 0.5:
        errors.append(
            f"片頭＋片尾後歌曲只剩 {song_window:.3f}s；至少須保留 0.5s"
        )
    for kind, label in (("vo", "口白"), ("sfx", "環境音")):
        for index, item in enumerate(cues_data.get(kind, []), 1):
            start = float(item.get("start", 0.0))
            duration = float(item["dur"])
            end = start + duration
            if start < 0:
                errors.append(f"{label} #{index} 起點 {start:.3f}s 小於 0")
            if end > total_dur:
                errors.append(
                    f"{label} #{index} 結束 {end:.3f}s 超出成片總長 {total_dur:.3f}s"
                )
    if errors:
        print("[ERR] 微電影時間軸不合法：")
        for error in errors:
            print(f"      {error}")
        sys.exit(1)
    return max(0.5, song_window)


def validate_dialog_srt(entries, vo_spans):
    """對白字幕要對得上某一段口白：起點不早於口白 DIALOG_LEAD 秒、終點不晚於口白結束後 DIALOG_TAIL 秒。
    擋的是「字幕對錯段／整份沒平移」這種錯，不是要求字幕跟音檔逐毫秒等長——
    字幕本來就常比語音多留一點閱讀時間，原本 0.05 秒容差會把正常做法誤擋。"""
    if not entries:
        return
    if not vo_spans:
        print("[ERR] 指定 --sub-dialog 時，--audio-cues 必須至少提供一段 vo 口白音檔")
        sys.exit(1)
    invalid = []
    for index, (start, end, _text) in enumerate(entries, 1):
        covered = any(
            start >= vo_start - DIALOG_LEAD
            and end <= vo_end + DIALOG_TAIL
            for vo_start, vo_end in vo_spans
        )
        if not covered:
            invalid.append(f"對白字幕 #{index} {start:.3f}s–{end:.3f}s 對不上任何 vo 口白"
                           f"（容許早 {DIALOG_LEAD}s 出現、晚 {DIALOG_TAIL}s 消失）")
    if invalid:
        print("[ERR] 對白字幕時間軸不合法：")
        for error in invalid:
            print(f"      {error}")
        sys.exit(1)


def duck_expr(intervals_rel, duck_vol):
    """音樂音量表達式：每段口白前 DUCK_ATTACK 秒線性壓到 duck_vol，結束後 DUCK_RELEASE 秒線性推回。
    原本是 if(between()) 瞬間跳 1.0↔0.22，會有音量階梯甚至喀聲。"""
    parts = []
    for s, e in intervals_rel:
        down = f"clip((t-{s - DUCK_ATTACK:.3f})/{DUCK_ATTACK},0,1)"
        up = f"clip(({e + DUCK_RELEASE:.3f}-t)/{DUCK_RELEASE},0,1)"
        parts.append(f"{down}*{up}")
    amount = parts[0]
    for p in parts[1:]:
        amount = f"max({amount},{p})"
    return f"1-{1 - duck_vol:.3f}*{amount}"


def normalize_audio(ffmpeg, music, total_dur, tmp_dir, prologue_sec=0.0, epilogue_sec=0.0, cues_data=None):
    """音樂裁到歌曲區間、結尾 2 秒淡出，支援微電影 Prologue 延遲、口白 Ducking 與 SFX 混音，再兩段式拉到 TARGET_LUFS。

    兩段式：loudnorm 先粗調 → ebur128 量實際值 → 補差額 → 限幅。
    alimiter 一定要 level=false：預設 level=true 會把輸出自動拉到 0 dBFS（爆音邊緣），而且不會報錯。
    """
    cues_data = cues_data or {}
    vo_list = cues_data.get("vo", [])
    sfx_list = cues_data.get("sfx", [])
    duck_vol = float(cues_data.get("music_duck_volume", 0.22))

    song_dur = max(0.5, total_dur - prologue_sec - epilogue_sec)
    music_filters = [f"afade=t=out:st={max(0.0, song_dur - 2.0):.2f}:d=2.0"]

    # 口白期間壓低音樂；區間換算成相對歌曲開頭（adelay 之前套用）
    rel = [(s - prologue_sec, e - prologue_sec) for s, e, _ in vo_intervals(cues_data)]
    rel = [(s, e) for s, e in rel if e + DUCK_RELEASE > 0 and s - DUCK_ATTACK < song_dur]
    if rel:
        music_filters.append(f"volume='{duck_expr(rel, duck_vol)}':eval=frame")

    if prologue_sec > 0:
        delay_ms = int(round(prologue_sec * 1000))
        music_filters.append(f"adelay={delay_ms}|{delay_ms}")
    music_filters.append(f"apad=whole_dur={total_dur:.3f}")

    music_bed = tmp_dir / "music_bed.wav"
    # 第一個 -t 放在 -i 前面才是裁輸入（放後面會被第二個 -t 蓋掉）
    run_ff([str(ffmpeg), "-y", "-t", f"{song_dur:.3f}", "-i", str(music),
            "-af", ",".join(music_filters),
            "-t", f"{total_dur:.3f}", "-ar", "48000", "-ac", "2", str(music_bed)])

    # 口白與音效逐軌對齊時間後與 music_bed 混音
    mix_inputs = [music_bed]
    for idx, item in enumerate(vo_list + sfx_list):
        is_vo = idx < len(vo_list)
        du = item["dur"]
        start_ms = int(round(float(item.get("start", 0.0)) * 1000))
        af = [f"volume={float(item.get('gain_db', 0.0)):.2f}dB"]
        # 口白頭尾預設 50／80ms 淡入淡出，避免硬切喀聲（記憶：旁白間的異音）
        fi = float(item.get("fade_in") or (0.05 if is_vo else 0))
        fo = float(item.get("fade_out") or (0.08 if is_vo else 0))
        if fi:
            af.append(f"afade=t=in:st=0:d={fi:.2f}")
        if fo:
            af.append(f"afade=t=out:st={max(0.0, du - fo):.2f}:d={fo:.2f}")
        if start_ms > 0:
            af.append(f"adelay={start_ms}|{start_ms}")
        af.append(f"apad=whole_dur={total_dur:.3f}")
        track_wav = tmp_dir / f"cue_{idx:02d}.wav"
        run_ff([str(ffmpeg), "-y", "-t", f"{du:.3f}", "-i", str(item["path"]),
                "-af", ",".join(af), "-t", f"{total_dur:.3f}", "-ar", "48000", "-ac", "2", str(track_wav)])
        mix_inputs.append(track_wav)

    if len(mix_inputs) > 1:
        pre_ln = tmp_dir / "pre_ln.wav"
        in_args = []
        for p_in in mix_inputs:
            in_args += ["-i", str(p_in)]
        run_ff([str(ffmpeg), "-y", *in_args,
                "-filter_complex", f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0:normalize=0",
                "-ar", "48000", str(pre_ln)])
        print(f"       已混入微電影音軌：音樂 + {len(vo_list)} 段口白 + {len(sfx_list)} 段環境音")
    else:
        pre_ln = music_bed

    ln = tmp_dir / "ln.wav"
    final = tmp_dir / "final.wav"
    run_ff([str(ffmpeg), "-y", "-i", str(pre_ln), "-t", f"{total_dur:.3f}",
            "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11",
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

_SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def _read_text_any(path):
    """SRT 可能是記事本存的 UTF-16（開頭 FF FE），也可能有 BOM"""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def read_srt(path):
    """回傳 [(start, end, text)]"""
    out = []
    for block in re.split(r"\r?\n\s*\r?\n", _read_text_any(path).strip()):
        lines = block.strip().splitlines()
        for i, line in enumerate(lines):
            m = _SRT_TIME.search(line)
            if m:
                g = [int(x) for x in m.groups()]
                s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                out.append((s, e, "\n".join(lines[i + 1:])))
                break
    return out


def write_srt(entries, path):
    def ts(t):
        ms = int(round(max(0.0, t) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for n, (s, e, text) in enumerate(entries, 1):
            f.write(f"{n}\n{ts(s)} --> {ts(e)}\n{text}\n\n")


def prepare_lyrics_srt(src, dst, offset, blocked_spans):
    """歌詞 SRT 是以歌曲開頭為 0（audio-to-srt 產的），整份平移 offset（＝片頭戲秒數）；
    跟口白重疊的歌詞條目拿掉，畫面上同一時間只留一種字幕（mv-14 規範）。"""
    kept, dropped = [], 0
    for s, e, text in read_srt(src):
        s, e = s + offset, e + offset
        if any(s < ve and e > vs for vs, ve in blocked_spans):
            dropped += 1
            continue
        kept.append((s, e, text))
    write_srt(kept, dst)
    return len(kept), dropped


def prepend_cover(ffmpeg, cover, sec, body, out):
    """封面靜圖（縮放到成片尺寸、頭尾各 0.5 秒淡入淡出）＋同長度靜音，接在 body 前面輸出到 out。"""
    fade = min(0.5, sec / 4)
    fc = (f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
          f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1,"
          f"fade=t=in:st=0:d={fade},fade=t=out:st={sec - fade}:d={fade}[cv];"
          f"[2:v]setsar=1[mv];[2:a]aresample=48000[ma];[cv][1:a][mv][ma]concat=n=2:v=1:a=1[v][a]")
    cmd = [str(ffmpeg), "-nostdin", "-loglevel", "error", "-y", "-loop", "1", "-t", f"{sec:.3f}", "-i", str(cover),
           "-f", "lavfi", "-t", f"{sec:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(body), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] 接封面失敗：{r.stderr[-600:]}")
        return False
    return True


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
    p.add_argument("--fit", help="首尾幀鏡頭（逗號分隔，如 cut28,cut42）：比分鏡長就加速塞進去、不剪後半；"
                                 "--shots 裡有 cutNN_last.* 的鏡會自動算進來")
    p.add_argument("--prologue", type=float, default=None, help="微電影：片頭前導戲秒數（音樂延遲幾秒才進場）")
    p.add_argument("--epilogue", type=float, default=None, help="微電影：片尾餘韻秒數（音樂結束後留幾秒環境音或畫面）")
    p.add_argument("--audio-cues", help="微電影：口白與環境音設定檔 audio_cues.json（含 VO 自動閃避音樂與 SFX 混音）")
    p.add_argument("--sub-lyrics", help="歌詞字幕 SRT（以歌曲開頭為 0；有片頭戲會自動平移，與口白重疊的條目自動拿掉）")
    p.add_argument("--lyrics-offset", type=float, default=None, help="歌詞 SRT 平移秒數（預設＝片頭戲秒數；SRT 已經對好成片時間軸就給 0）")
    p.add_argument("--sub-dialog", help="微電影：對白／口白字幕 SRT（以成片時間軸為 0，不平移）")
    p.add_argument("--cover", help="片頭封面圖（標題＋署名），接在第一鏡前面、靜音；字幕與口白時間軸不受影響")
    p.add_argument("--cover-sec", type=float, default=3.0, help="封面秒數（預設 3，含頭尾各 0.5 秒淡入淡出）")
    p.add_argument("--music", required=True)
    p.add_argument("--out",   required=True)
    args = p.parse_args()
    if args.cover and not Path(args.cover).exists():
        p.error(f"找不到封面 {args.cover}")
    ALLOW_LOWRES, ALLOW_FPS = args.allow_lowres, args.allow_fps
    if args.storyboard:
        import storyboard_md
        STORYBOARD = storyboard_md.load_or_exit(args.storyboard)
    WIDTH, HEIGHT = map(int, args.size.lower().split("x"))
    if not args.shots and not args.videos:
        p.error("--shots 和 --videos 至少要給一個")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("[ERR] ffmpeg 不在 PATH"); sys.exit(1)
    print(f"  ffmpeg: {ffmpeg}")

    shots = Path(args.shots).resolve() if args.shots else None
    videos = Path(args.videos).resolve() if args.videos else None
    fit_cuts = {c.strip() for c in (args.fit or "").split(",") if c.strip()}
    music = Path(args.music).resolve()
    out_path = Path(args.out).resolve()   # 絕對路徑：concat 清單裡的相對路徑會以清單檔所在處為準
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / "tmp_kb"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(exist_ok=True)

    cues_data = load_cues(Path(args.audio_cues).resolve()) if args.audio_cues else {}
    prologue_sec = args.prologue if args.prologue is not None else float(cues_data.get("prologue_sec", 0.0))
    epilogue_sec = args.epilogue if args.epilogue is not None else float(cues_data.get("epilogue_sec", 0.0))

    total_dur = sum(s[4] for s in STORYBOARD)
    song_window = validate_mix_timeline(cues_data, total_dur, prologue_sec, epilogue_sec)
    music_dur = probe_duration(music)
    if music_dur + 0.05 < song_window:
        print(f"[ERR] 音樂 {music_dur:.2f}s 比所需歌曲區間 {song_window:.2f}s（總長 {total_dur:.2f}s - 片頭 {prologue_sec:.1f}s - 片尾 {epilogue_sec:.1f}s）短，片尾會沒聲音。"
              "先改 STORYBOARD 秒數或 --prologue/--epilogue（MV_11 規定）")
        sys.exit(1)
    if music_dur - song_window > 0.25:
        print(f"  [注意] 音樂 {music_dur:.2f}s 比歌曲區間 {song_window:.2f}s 長，"
              f"會在歌曲區間結束處淡出，歌的最後 {music_dur - song_window:.1f}s 不會出現")
    print(f"\n== 開始組裝 MV ==")
    print(f"  素材：{shots}")
    print(f"  音樂：{music.name}")
    print(f"  cut 數：{len(STORYBOARD)}，總長：{total_dur}s（片頭戲 {prologue_sec:.1f}s / 歌曲 {song_window:.1f}s / 片尾戲 {epilogue_sec:.1f}s）")
    print(f"  解析度：{WIDTH}x{HEIGHT}  FPS：{FPS}")

    # Step 1: 12 個 cut
    print(f"\n  Step 1: 每鏡做成短片（有影片用影片，沒有才用圖做 Ken Burns）...")
    clip_paths = []
    for i, (prefix, anim, t_in, t_out, dur) in enumerate(STORYBOARD):
        clip = tmp / f"clip_{i:02d}.mp4"
        vid = find_video(videos, prefix)
        if vid:
            print(f"  [{i+1:02d}/{len(STORYBOARD)}] {prefix} -> 影片 {vid.name} ({t_in}/{t_out}) {dur}s")
            ok = make_video_clip(ffmpeg, vid, t_in, t_out, dur, clip,
                                 fit=has_last_frame(shots, prefix, fit_cuts))
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

    # Step 3: 音樂裁到分鏡長度、結尾淡出、微電影混音與兩段式響度
    print(f"\n  Step 3: 音軌混音與響度標準化（目標 {TARGET_LUFS} LUFS）...")
    final_wav = normalize_audio(ffmpeg, music, total_dur, tmp, prologue_sec, epilogue_sec, cues_data)

    # Step 4: 組合最終 MP4（可選燒錄歌詞與對白雙層字幕）
    # 字幕先複製到 tmp、ffmpeg 在 tmp 底下跑，濾鏡裡只寫檔名——避開 Windows 磁碟代號冒號的跳脫問題
    vf_subs = []
    dialog_entries = []
    vo_spans = [(s, e) for s, e, _ in vo_intervals(cues_data)]
    if args.sub_dialog:
        dialog_entries = read_srt(Path(args.sub_dialog))
        validate_dialog_srt(dialog_entries, vo_spans)
    if args.sub_lyrics:
        offset = prologue_sec if args.lyrics_offset is None else args.lyrics_offset
        # 對白字幕可比口白多留閱讀時間，所以要把字幕自身區間也列入避讓，否則會留下雙字幕。
        blocked_spans = vo_spans + [(s, e) for s, e, _ in dialog_entries]
        n_keep, n_drop = prepare_lyrics_srt(Path(args.sub_lyrics), tmp / "lyrics.srt", offset, blocked_spans)
        print(f"       歌詞字幕：平移 {offset:+.2f}s，{n_keep} 條；與口白重疊拿掉 {n_drop} 條")
        vf_subs.append("subtitles=lyrics.srt:force_style='FontName=Microsoft JhengHei,FontSize=20,PrimaryColour=&H00E0FFFF,OutlineColour=&H00000000,Outline=2,MarginV=55'")
    if args.sub_dialog:
        write_srt(dialog_entries, tmp / "dialog.srt")
        vf_subs.append("subtitles=dialog.srt:force_style='FontName=Microsoft JhengHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=25'")

    cmd = [
        str(ffmpeg), "-nostdin", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(final_wav),
    ]
    if vf_subs:
        cmd += ["-vf", ",".join(vf_subs)]
    body_path = tmp / "body.mp4" if args.cover else out_path
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_dur:.3f}",
        str(body_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp),
                       encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(f"  [FFMPEG ERROR] {r.stderr[-600:]}"); sys.exit(1)

    # Step 5: 片頭封面——等字幕燒完才接，字幕／口白時間軸都以第一鏡為 0，不用跟著平移
    if args.cover:
        print(f"\n  Step 5: 接上片頭封面 {Path(args.cover).name}（{args.cover_sec:g} 秒、靜音）...")
        if not prepend_cover(ffmpeg, Path(args.cover).resolve(), args.cover_sec, body_path, out_path):
            sys.exit(1)

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
