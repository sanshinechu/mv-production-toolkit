import os, subprocess
from pathlib import Path

BASE_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作")
ORIG_MOVIE = BASE_DIR / "腳底下的小河冒險記_完整有聲微電影_1080p.mp4"
STEREO_MOVIE = BASE_DIR / "腳底下的小河冒險記_有聲微電影_標準雙聲道48k.mp4"

# 轉成 48000Hz 立體聲 (2 channels) 並使用 loudnorm 響度最佳化（達到 YouTube / 標準播放器音量 -14 LUFS）
print("Converting audio to 48000Hz Stereo with loudnorm...")

# 先抽音軌並升採樣為雙聲道標準音軌
cmd = [
    "ffmpeg", "-y",
    "-i", str(ORIG_MOVIE),
    "-c:v", "copy",
    "-af", "aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-14:LRA=11:TP=-1.5",
    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
    str(STEREO_MOVIE)
]
subprocess.run(cmd, check=True)
print(f"Done! Created: {STEREO_MOVIE} ({STEREO_MOVIE.stat().st_size / 1024 / 1024:.2f} MB)")
