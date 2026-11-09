import json

path = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\音軌_v1\story_audio_timeline.json"
data = json.load(open(path, encoding="utf-8"))
total = 0.0
for p in data:
    sec = p["total_duration"]
    total += sec
    print(f"Page {p['page']:02d}: {sec:>5.1f}s ({sec/60:4.2f} min) | {len(p['lines'])} lines")

print(f"\nTotal story duration: {total:.1f}s = {total/60:.2f} min ({int(total//60)} 分 {int(total%60)} 秒)")
