import json
from pathlib import Path

timeline_file = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\音軌_v1\story_audio_timeline.json")
data = json.loads(timeline_file.read_text(encoding="utf-8"))

def sec_to_srt_time(sec):
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    millis = int((sec - int(sec)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

srt_entries = []
srt_idx = 1
current_global_time = 0.0

for p_info in data:
    p_num = p_info["page"]
    lines = p_info["lines"]
    
    page_start_time = current_global_time
    line_time = page_start_time
    
    for l in lines:
        role = l["role"]
        text = l["text"]
        dur = l["duration"]
        
        start_str = sec_to_srt_time(line_time)
        end_str = sec_to_srt_time(line_time + dur)
        
        # 旁白不加前綴，角色台詞標注角色名
        if role == "旁白":
            caption = text
        else:
            caption = f"【{role}】{text}"
            
        srt_entries.append(f"{srt_idx}\n{start_str} --> {end_str}\n{caption}\n")
        srt_idx += 1
        line_time += dur
        
    current_global_time += p_info["total_duration"]

out_srt = timeline_file.parent / "nanmen_story_full.srt"
out_srt.write_text("\n".join(srt_entries), encoding="utf-8")
print(f"Generated SRT: {out_srt} with {len(srt_entries)} subtitle cues.")
