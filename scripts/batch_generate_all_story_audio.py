import os, sys, time, json, base64, urllib.request, subprocess
from pathlib import Path
from google.oauth2 import service_account
import google.auth.transport.requests

OUT_DIR = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\音軌_v1")
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_LINES_FILE = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\story_lines.json")

# 讀取 Vertex / Google Cloud 憑證
env = {}
for line in open(os.path.expanduser('~/.vertexai.env'), encoding='utf-8'):
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.strip().split('=', 1)
        env[k] = v.strip().strip('"')

cred = service_account.Credentials.from_service_account_file(
    env['GOOGLE_APPLICATION_CREDENTIALS'], scopes=['https://www.googleapis.com/auth/cloud-platform'])
cred.refresh(google.auth.transport.requests.Request())
TOKEN = cred.token
PROJECT = env['GOOGLE_CLOUD_PROJECT']

ROLE_CONFIG = {
    "旁白": {
        "voice": "Puck",
        "style": "台灣溫暖的說故事旁白老師，語速適中偏慢，溫和親切，自然台灣國語口音"
    },
    "阿東伯": {
        "voice": "Charon",
        "style": "台灣的慈祥老爺爺，聲音低沉溫和，說話慢慢的、咬字清楚，自然的台灣國語口音"
    },
    "小東": {
        "voice": "Zephyr",
        "style": "台灣國小五年級、十一歲的小男孩，童聲，活潑好奇、有精神，咬字清楚，自然的台灣國語口音"
    },
    "羅絲": {
        "voice": "Zephyr",
        "style": "台灣國小五年級、十一歲的小女孩，童聲，細心可愛、有精神，咬字清楚，自然的台灣國語口音"
    },
    "阿波": {
        "voice": "Aoede",
        "style": "可愛活潑的南門河守護小水滴精靈，聲音童趣清亮，像卡通精靈角色，高興熱情"
    }
}

def get_valid_token():
    global TOKEN
    try:
        cred.refresh(google.auth.transport.requests.Request())
        TOKEN = cred.token
    except Exception as e:
        print("Token refresh note:", e)
    return TOKEN

def synth_line(role, text, out_file):
    if out_file.exists() and out_file.stat().st_size > 1000:
        return True

    cfg = ROLE_CONFIG.get(role, ROLE_CONFIG["旁白"])
    prompt = cfg["style"] + "。只念一次，不要加字、不要重複。"
    
    body = {
        "input": {"prompt": prompt, "text": text},
        "voice": {"languageCode": "cmn-TW", "name": cfg["voice"], "modelName": "gemini-2.5-flash-tts"},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000}
    }
    
    for attempt in range(5):
        token = get_valid_token()
        req = urllib.request.Request(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "x-goog-user-project": PROJECT}
        )
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                res = json.load(r)
                out_file.write_bytes(base64.b64decode(res["audioContent"]))
            return True
        except urllib.error.HTTPError as e:
            print(f"    [HTTP {e.code}] on attempt {attempt+1}")
            if e.code == 429:
                time.sleep(12 * (attempt + 1))
            else:
                time.sleep(3)
        except Exception as e:
            print(f"    [Error] {e} on attempt {attempt+1}")
            time.sleep(3)
    return False

def get_audio_duration(wav_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0

def main():
    pages = json.loads(RAW_LINES_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(pages)} pages.")

    timeline_data = []
    
    for p_info in pages:
        p_num = p_info["page"]
        lines = p_info["lines"]
        print(f"\n==================== Page {p_num:02d} ({len(lines)} lines) ====================")
        
        page_items = []
        concat_list_file = OUT_DIR / f"concat_p{p_num:02d}.txt"
        with open(concat_list_file, "w", encoding="utf-8") as concat_f:
            for idx, (role, text) in enumerate(lines, 1):
                clean_text = text.strip()
                out_wav = OUT_DIR / f"p{p_num:02d}_{idx:02d}_{role}.wav"
                # 安全印出避免 cp950 報錯
                safe_text = clean_text[:35].encode("ascii", "replace").decode("ascii")
                print(f"  [{idx:02d}] {role}: {safe_text}...")
                
                ok = synth_line(role, clean_text, out_wav)
                if not ok:
                    print(f"    [FAIL] Could not synthesize line {idx}")
                    continue
                
                dur = get_audio_duration(out_wav)
                page_items.append({
                    "page": p_num,
                    "index": idx,
                    "role": role,
                    "text": clean_text,
                    "file": out_wav.name,
                    "duration": dur
                })
                # 加入清單供 ffmpeg 串接，每句之間留 0.35 秒間隔
                concat_f.write(f"file '{out_wav.name}'\n")
                
                # 禮貌延遲防 429
                time.sleep(1.5)

        # 串接該頁完整音軌
        page_mp3 = OUT_DIR / f"p{p_num:02d}_full.mp3"
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_file), "-c:a", "libmp3lame", "-q:a", "2", str(page_mp3)]
        subprocess.run(cmd, capture_output=True)
        p_dur = get_audio_duration(page_mp3)
        print(f"  --> Page {p_num:02d} Full MP3 generated: {page_mp3.name} ({p_dur:.1f}s)")
        
        timeline_data.append({
            "page": p_num,
            "total_duration": p_dur,
            "lines": page_items
        })

    # 儲存全片時間軸與字幕資訊
    out_timeline = OUT_DIR / "story_audio_timeline.json"
    out_timeline.write_text(json.dumps(timeline_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAll Done! Saved timeline to {out_timeline}")

if __name__ == "__main__":
    main()
