# -*- coding: utf-8 -*-
r"""《半張車票》口白修時長 → 產 dialog.srt 與 audio_cues.json（給 make_mv.py／review_mv.py 吃）。

用法（cmd）：
  python scripts/prepare_audio_cues_and_subs.py --project outputs/半張車票   # 相對路徑：以 01_MV製作 為基準
  python scripts/prepare_audio_cues_and_subs.py --project <當台封存區>\半張車票  # 絕對路徑：專案已搬到當台封存區時

- 讀 <專案>/audio/vo_*.wav（TTS 出來的原檔），trim 靜音、太長的用 atempo 壓到 max_dur，
  輸出 <專案>/audio/vo_*_clean.wav、<專案>/dialog.srt、<專案>/audio_cues.json。
- audio_cues.json 裡的檔名一律寫成 `audio/xxx.wav` 這種相對寫法，以 <專案> 為基準。
- 路徑不寫死：各機碟號不同，而且專案上架後還會搬到當台封存區（見 docs/影片分流策略.md）。
- 音效要先跑 build_half_ticket_sfx.py --project <同一個專案> 生好。
"""
import os, sys, json, subprocess, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 參數解析與路徑檢查刻意排在第三方 import 前面：沒裝 librosa 的機器也要能跑 --help，
# 專案路徑給錯時也才會先看到下面那句錯誤，而不是 ModuleNotFoundError。
_ap = argparse.ArgumentParser(description="《半張車票》口白修時長與 cues 產生")
_ap.add_argument("--project", required=True,
                 help=r"專案資料夾：絕對路徑，或相對於 01_MV製作（例如 outputs\半張車票）")
_args = _ap.parse_args()
_project = Path(_args.project)
if not _project.is_absolute():
    _project = ROOT / _project
MV_DIR = str(_project)
AUDIO_DIR = str(_project / "audio")
if not os.path.isdir(AUDIO_DIR):
    sys.exit(f"[ERROR] 找不到 {AUDIO_DIR}。--project 要指到專案資料夾（底下要有 audio/，口白原檔放在裡面）")
print(f"[DIR] 專案 {MV_DIR}")

import librosa, soundfile as sf

PROLOGUE = 55.0
EPILOGUE = 40.0

# 20 lines specification (含 4s 阿福自白Part A/B、15.5s 開過頭、20.2s 站牌自白)
VO_PLAN = [
    # id, text, start, max_dur
    ("vo_00a_afu", "我是阿福，在羅東開公車已經 40 年了，", 0.7, 4.0),
    ("vo_00b_afu", "每晚……都在這裡載大家回家。", 4.8, 3.5),
    ("vo_00_afu_overshoot", "糟糕！我開過頭了", 12.5, 2.5),
    ("vo_01_afu", "真是的，不小心把車子開過站，小朋友呢？", 17.2, 5.0),
    ("vo_02_azhong", "阿福，又淋成這樣？", 24.6, 3.0),
    ("vo_03_afu", "今天有個孩子，我沒停好。", 28.3, 3.4),
    ("vo_04_azhong", "你那隻手，該去給醫生看了。", 32.3, 3.4),
    ("vo_05_afu", "明天晚上開完最後一班車，我就把鑰匙交回去。", 36.1, 4.5),
    ("vo_06_azhong", "你工作 40 年了，也該為自己的健康著想。", 41.0, 6.0),
    ("vo_07_afu", "老夥伴，我們都老了。", 48.3, 2.5),
    ("vo_08_xiaowen", "阿福伯，這次換我們。", 162.7, 2.6),
    ("vo_09_afu", "……好。", 166.2, 1.8),
    ("vo_10_afu", "下車站……晴天？", 215.6, 3.5),
    ("vo_11_xiaowen", "今天開始，換你當乘客。", 220.0, 4.0),
    ("vo_12_ade", "阿福仔，明天來我家吃滷肉！", 224.8, 3.0),
    ("vo_13_sun", "阿公說你開車最穩！", 228.0, 2.8),
    ("vo_14_mom", "對不起，媽媽來晚了。", 242.0, 2.8),
    ("vo_15_boy", "剛剛有一台公車想停下來載我", 245.2, 3.2),
    ("vo_16_mom", "那下次，我們跟司機說謝謝。", 248.6, 3.0),
    ("vo_17_driver", "伯伯早！慢慢來，不急。", 256.2, 2.6),
    ("vo_18_afu", "早。謝謝你。", 259.3, 2.4),
]

processed_vo = []

for vid, text, start, max_dur in VO_PLAN:
    raw_path = os.path.join(AUDIO_DIR, f"{vid}.wav")
    clean_path = os.path.join(AUDIO_DIR, f"{vid}_clean.wav")
    
    y, sr = librosa.load(raw_path, sr=48000)
    yt, _ = librosa.effects.trim(y, top_db=25)
    dur = len(yt) / sr
    
    # If dur exceeds max_dur, speed up with atempo
    if dur > max_dur:
        factor = dur / max_dur
        # save trimmed temp
        tmp_trim = os.path.join(AUDIO_DIR, f"{vid}_tmp.wav")
        sf.write(tmp_trim, yt, sr)
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp_trim,
            "-filter:a", f"atempo={factor:.3f}",
            "-ar", "48000", clean_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(tmp_trim)
        y_c, _ = librosa.load(clean_path, sr=48000)
        final_dur = len(y_c) / 48000
    else:
        sf.write(clean_path, yt, sr)
        final_dur = dur
        
    print(f"[VO] {vid}: start={start:.2f}s, dur={final_dur:.2f}s (max={max_dur:.2f}s)")
    processed_vo.append({
        "file": f"audio/{vid}_clean.wav",
        "start": round(start, 2),
        "dur": round(final_dur, 2),
        "gain_db": 1.5,
        "text": text
    })

# Format dialog.srt
def ts(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

srt_entries = []
for idx, v in enumerate(processed_vo, 1):
    s = v["start"]
    # dialogue subtitle appears at speech start and stays for reading time (+0.4s to +0.8s)
    # validate_dialog_srt allows early -0.2s and late +1.0s
    extra = 0.5
    tentative_e = round(s + v["dur"] + extra, 2)
    if idx < len(processed_vo):
        next_s = processed_vo[idx]["start"]
        # 避免與下一句字幕重疊：結束時間必須在下一句開始前至少 0.08s 關閉
        e = min(tentative_e, round(next_s - 0.08, 2))
    else:
        e = tentative_e
    if e <= s:
        e = round(s + v["dur"], 2)
    srt_entries.append(f"{idx}\n{ts(s)} --> {ts(e)}\n{v['text']}\n")

srt_path = os.path.join(MV_DIR, "dialog.srt")
with open(srt_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(srt_entries) + "\n")
print(f"[OK] Written {srt_path} ({len(srt_entries)} entries)")

# SFX Cues
SFX_PLAN = [
    ("audio/sfx_01_rain_wiper_engine.wav", 0.0, 24.0, -16.0, 0.5, 1.0),
    ("audio/sfx_02_brake_splash.wav", 8.5, 7.5, -17.0, 0.2, 0.5),
    ("audio/sfx_03_footsteps_water.wav", 16.5, 7.5, -17.0, 0.3, 0.5),
    ("audio/sfx_04_garage_ambient.wav", 24.0, 16.0, -20.0, 0.5, 0.5),
    ("audio/sfx_05_writing_footsteps.wav", 40.5, 7.5, -18.0, 0.2, 0.4),
    ("audio/sfx_06_tin_box.wav", 50.5, 4.5, -15.0, 0.1, 0.3),
    ("audio/sfx_07_ticket_tear.wav", 63.8, 2.0, -15.0, 0.05, 0.1),
    ("audio/sfx_08_engine_start.wav", 81.6, 2.4, -15.0, 0.1, 0.3),
    ("audio/sfx_09_door_air.wav", 124.6, 3.0, -15.0, 0.05, 0.2),
    ("audio/sfx_10_key_bell.wav", 176.0, 3.5, -14.0, 0.02, 0.3),
    ("audio/sfx_11_shutter_open.wav", 183.0, 3.5, -15.0, 0.2, 0.4),
    ("audio/sfx_12_morning_market.wav", 215.0, 21.84, -20.0, 0.5, 1.0),
    ("audio/sfx_13_rain_return.wav", 236.84, 15.0, -16.0, 0.5, 1.0),
    ("audio/sfx_14_bus_chime.wav", 252.0, 4.0, -14.0, 0.05, 0.5),
    ("audio/sfx_15_card_beep.wav", 262.2, 3.0, -14.0, 0.1, 0.5),
]

sfx_cues = []
for file_p, st, dur, gain, fi, fo in SFX_PLAN:
    sfx_cues.append({
        "file": file_p,
        "start": round(st, 2),
        "duration": round(dur, 2),
        "gain_db": gain,
        "fade_in": fi,
        "fade_out": fo
    })

# Full audio_cues.json
cues_data = {
    "prologue_sec": PROLOGUE,
    "epilogue_sec": EPILOGUE,
    "music_duck_volume": 0.22,
    "vo": processed_vo,
    "sfx": sfx_cues
}

cues_path = os.path.join(MV_DIR, "audio_cues.json")
with open(cues_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(cues_data, f, ensure_ascii=False, indent=2)
print(f"[OK] Written {cues_path} ({len(processed_vo)} VOs, {len(sfx_cues)} SFXs)")
