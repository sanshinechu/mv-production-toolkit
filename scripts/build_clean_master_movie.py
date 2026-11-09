import os, sys, time, json, subprocess
from pathlib import Path

# 2026-11-09 主機 1：路徑改從本檔往上推（原本寫死家裡用筆電的 C:\Users\user）；
# 字幕改燒 generate_srt_subtitles.py 產的 ASS（短句、像素字級）；加 --subs-only 只重做第 3 步。
BASE_DIR = Path(__file__).resolve().parents[2] / "10_科技競賽" / "115學年度" / "游智盃_南門河"
MV_DIR = BASE_DIR / "南門河_MV製作"
WORK_DIR = MV_DIR / "render_work"
AUDIO_DIR = BASE_DIR / "繪本影片" / "音軌_v1"

TIMELINE_FILE = AUDIO_DIR / "story_audio_timeline.json"
ASS_FILE = AUDIO_DIR / "nanmen_story_full.ass"

MASTER_AUDIO_WAV = WORK_DIR / "master_audio_continuous_48k.wav"
MASTER_VIDEO_MP4 = WORK_DIR / "master_video_continuous.mp4"
FINAL_CLEAN_MOVIE = MV_DIR / "腳底下的小河冒險記_完整有聲微電影_正式版_字幕分段.mp4"

def main():
    timeline = json.loads(TIMELINE_FILE.read_text(encoding="utf-8"))
    if "--subs-only" in sys.argv:
        return burn_subs()

    # 步驟 1：建立單一連續的完整音訊母帶
    print("=== Step 1: Building Continuous Master Audio ===")
    audio_concat_list = WORK_DIR / "audio_concat_clean.txt"
    with open(audio_concat_list, "w", encoding="utf-8") as f:
        for p in timeline:
            p_num = p["page"]
            mp3_path = AUDIO_DIR / f"p{p_num:02d}_full.mp3"
            f.write(f"file '{mp3_path.resolve()}'\n")

    # 重新解碼串接成連續的 48kHz 立體聲 WAV，並套用 loudnorm 標準化音量
    cmd_audio = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(audio_concat_list),
        "-af", "aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-14:LRA=11:TP=-1.5",
        "-c:a", "pcm_s16le",
        str(MASTER_AUDIO_WAV)
    ]
    subprocess.run(cmd_audio, check=True)
    print(f"Master audio generated: {MASTER_AUDIO_WAV} ({MASTER_AUDIO_WAV.stat().st_size / 1024 / 1024:.2f} MB)")

    # 步驟 2：串接 10 頁的純視訊畫面（丟棄各自的暫存音軌）
    print("\n=== Step 2: Building Continuous Master Video ===")
    video_concat_list = WORK_DIR / "video_concat_clean.txt"
    with open(video_concat_list, "w", encoding="utf-8") as f:
        for p in timeline:
            p_num = p["page"]
            # 使用先前已渲染好的 page_XX.mp4 的純視訊
            page_mp4 = WORK_DIR / f"page_{p_num:02d}.mp4"
            f.write(f"file '{page_mp4.resolve()}'\n")

    cmd_video = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(video_concat_list),
        "-an",  # 完全不要個別檔案的殘餘音軌
        "-c:v", "copy",
        str(MASTER_VIDEO_MP4)
    ]
    subprocess.run(cmd_video, check=True)
    print(f"Master video generated: {MASTER_VIDEO_MP4}")
    burn_subs()


def burn_subs():
    # 步驟 3：視訊 ＋ 純淨音訊母帶合流 ＋ 燒錄中文字幕
    # 字級與樣式寫在 ASS 檔裡（PlayResY=1080，像素單位）；cwd 切到字幕資料夾，濾鏡只寫檔名，免跳脫碟號冒號
    print("\n=== Step 3: Muxing Audio + Video + Burning Subtitles ===")
    vf_sub = f"ass={ASS_FILE.name}"

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(MASTER_VIDEO_MP4),
        "-i", str(MASTER_AUDIO_WAV),
        "-vf", vf_sub,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-shortest",
        str(FINAL_CLEAN_MOVIE)
    ]
    subprocess.run(cmd_final, check=True, cwd=ASS_FILE.parent)

    final_size = FINAL_CLEAN_MOVIE.stat().st_size / 1024 / 1024
    print(f"\nSUCCESS! Clean movie rendered: {FINAL_CLEAN_MOVIE} ({final_size:.2f} MB)")

if __name__ == "__main__":
    main()
