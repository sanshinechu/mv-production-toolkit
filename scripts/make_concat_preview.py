import os, subprocess

video_dir = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw"
list_file = os.path.join(video_dir, "concat_list.txt")

with open(list_file, "w", encoding="utf-8") as f:
    for i in range(1, 11):
        f.write(f"file 'p{i:02d}_flow.mp4'\n")

out_mp4 = os.path.join(video_dir, "南門河_10鏡動態總覽_無損組裝.mp4")
cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out_mp4]
res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg returncode:", res.returncode)
if os.path.exists(out_mp4):
    print(f"Created: {out_mp4} ({os.path.getsize(out_mp4)/1024/1024:.2f} MB)")
