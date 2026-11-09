import os, sys, time, json, subprocess
from pathlib import Path

BASE_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河")
MV_DIR = BASE_DIR / "南門河_MV製作"
VIDEOS_RAW = MV_DIR / "videos-raw"
SHOTS_DIR = MV_DIR / "shots"
AUDIO_DIR = BASE_DIR / "繪本影片" / "音軌_v1"
WORK_DIR = MV_DIR / "render_work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

TIMELINE_FILE = AUDIO_DIR / "story_audio_timeline.json"
FINAL_OUT = MV_DIR / "腳底下的小河冒險記_完整有聲微電影_1080p.mp4"

PAGE_IMAGES = {
    1: ["p01_阿束社水溝蓋的好奇心.png"],
    2: ["p02_大石頭阿東伯登場.png"],
    3: ["p03_阿束社原野.png"],
    4: ["p04_船仔頭碼頭.png"],
    5: ["p05_洗衫橋.png"],
    6: ["p06_端午龍舟賽.png"],
    7: ["p07_南門河畫冊.png"],
    8: ["p08_加蓋.png"],
    9: ["p09_大石頭踏查.png"],
    10: ["p10_電腦教室.png", "p10_未來親水公園_想像畫面.png"],
}

def get_duration(media_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.0

def make_kenburns_clip(img_path, duration, out_path):
    if out_path.exists() and out_path.stat().st_size > 100_000:
        return
    frames = int(duration * 24)
    vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0002,1.08)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=24"
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
        "-vf", vf, "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24",
        str(out_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def render_page(p_info):
    p_num = p_info["page"]
    audio_file = AUDIO_DIR / f"p{p_num:02d}_full.mp3"
    total_audio_dur = p_info["total_duration"]
    flow_video = VIDEOS_RAW / f"p{p_num:02d}_flow.mp4"
    flow_dur = min(10.0, get_duration(flow_video))
    
    out_page_mp4 = WORK_DIR / f"page_{p_num:02d}.mp4"
    if out_page_mp4.exists() and out_page_mp4.stat().st_size > 1_000_000:
        print(f"Page {p_num:02d} already rendered, skipping.")
        return out_page_mp4

    print(f"\n--- Rendering Page {p_num:02d} (Total audio: {total_audio_dur:.1f}s) ---")
    rem_dur = max(0.5, total_audio_dur - flow_dur)
    
    img_names = PAGE_IMAGES[p_num]
    kb_clips = []
    
    if len(img_names) == 1:
        img_path = SHOTS_DIR / img_names[0]
        kb_out = WORK_DIR / f"kb_p{p_num:02d}.mp4"
        make_kenburns_clip(img_path, rem_dur, kb_out)
        kb_clips.append(kb_out)
    else:
        # 第 10 頁拆成兩張圖片
        dur_part1 = rem_dur / 2.0
        dur_part2 = rem_dur - dur_part1
        
        img1 = SHOTS_DIR / img_names[0]
        img2 = SHOTS_DIR / img_names[1]
        
        kb_out1 = WORK_DIR / f"kb_p{p_num:02d}_1.mp4"
        kb_out2 = WORK_DIR / f"kb_p{p_num:02d}_2.mp4"
        
        make_kenburns_clip(img1, dur_part1, kb_out1)
        make_kenburns_clip(img2, dur_part2, kb_out2)
        
        kb_clips.extend([kb_out1, kb_out2])

    # 產生該頁視訊拼接清單
    concat_list = WORK_DIR / f"concat_p{p_num:02d}.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        f.write(f"file '{flow_video.resolve()}'\n")
        for clip in kb_clips:
            f.write(f"file '{clip.resolve()}'\n")

    # 將 Flow 影片 + Ken Burns + 音軌合流
    # 注意 Flow 影片本身原聲靜音，只保留配音母帶
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(audio_file),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_page_mp4)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Page {p_num:02d} rendered: {out_page_mp4.name} ({get_duration(out_page_mp4):.1f}s)")
    return out_page_mp4

def main():
    timeline = json.loads(TIMELINE_FILE.read_text(encoding="utf-8"))
    page_files = []
    
    for p_info in timeline:
        mp4 = render_page(p_info)
        page_files.append(mp4)

    print("\n==================== Concatenating All 10 Pages ====================")
    full_concat_list = WORK_DIR / "full_story_concat.txt"
    with open(full_concat_list, "w", encoding="utf-8") as f:
        for p_file in page_files:
            f.write(f"file '{p_file.resolve()}'\n")

    # 串接 10 頁成完整視訊母帶
    temp_full = WORK_DIR / "story_full_no_sub.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(full_concat_list),
        "-c", "copy",
        str(temp_full)
    ]
    subprocess.run(cmd_concat, check=True, capture_output=True)
    print(f"Full concatenated video ready: {temp_full.name} ({get_duration(temp_full):.1f}s)")

    print("\n==================== Burning Subtitles ====================")
    srt_file = AUDIO_DIR / "nanmen_story_full.srt"
    # Windows 路徑在 subtitles 濾鏡中跳脫冒號與反斜線
    srt_filter_path = str(srt_file.resolve()).replace("\\", "/").replace(":", "\\:")
    
    # 字幕樣式：微軟正黑體粗體，字體大小 24，亮黃色字帶黑色描邊與半透明底框
    sub_style = "Fontname=Microsoft JhengHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=1,Alignment=2,MarginV=35"
    vf_sub = f"subtitles='{srt_filter_path}':force_style='{sub_style}'"

    cmd_sub = [
        "ffmpeg", "-y",
        "-i", str(temp_full),
        "-vf", vf_sub,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(FINAL_OUT)
    ]
    subprocess.run(cmd_sub, check=True, capture_output=True)
    
    final_dur = get_duration(FINAL_OUT)
    final_size_mb = FINAL_OUT.stat().st_size / 1024 / 1024
    print(f"\n🎉 ALL COMPLETE! Final Output:")
    print(f"  Path: {FINAL_OUT}")
    print(f"  Duration: {final_dur:.1f}s ({final_dur/60:.2f} min)")
    print(f"  Size: {final_size_mb:.2f} MB")

if __name__ == "__main__":
    main()
