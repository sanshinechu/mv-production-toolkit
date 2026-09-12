"""驅動本地 HeartMuLa Studio 生歌，不用開 UI 手點。

    uv run --with requests python heartmula_gen.py --lyrics 歌詞.txt --tags "live rock, ..." --n 4

用途：歌詞有版權、Suno 會擋的時候，改在本地跑。HeartMuLa 沒有內容過濾，
中文歌詞直接貼。⚠️ 但它**不會照原曲旋律唱**——ref_audio 走的是 MuQ 風格嵌入，
抄的是氛圍不是音符。要保留原旋律請改走 Suno Cover 那條（見 ../README.md）。

歌詞從檔案讀進來直接送 API，不會印在畫面上，也不會進版控。

後端沒開的話腳本會告訴你怎麼開。
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"
APP = r"D:\pinokio\api\heartmula-studio.git\app"

START_HINT = rf"""
後端沒有回應。開一個 PowerShell 視窗跑：

  cd "{APP}"
  $env:PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
  $env:HEARTMULA_4BIT="auto"
  $env:HEARTMULA_SEQUENTIAL_OFFLOAD="auto"
  $env:HEARTMULA_COMPILE="false"
  venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

或在 Pinokio 裡按 HeartMuLa Studio 的 Start。
第一次載模型要等，8GB 卡會走 4-bit ＋ 循序卸載，每首多約 70 秒。
"""


def health():
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        return r.ok
    except requests.RequestException:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lyrics", required=True, help="歌詞純文字檔（UTF-8）")
    ap.add_argument("--tags", required=True, help="曲風標籤，例：live rock, mandopop, female vocal")
    ap.add_argument("--prompt", default=None, help="整句風格描述，不給就用 tags")
    ap.add_argument("--title", default=None)
    ap.add_argument("--duration-sec", type=float, default=240)
    ap.add_argument("--n", type=int, default=1, help="生幾首（同設定多生幾首再挑）")
    ap.add_argument("--seed", type=int, default=None, help="固定種子，不給每首用不同隨機種子")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--cfg-scale", type=float, default=1.5)
    ap.add_argument("--ref-audio-id", default=None,
                    help="參考音訊 ID（先用 /upload/ref_audio 上傳）。注意這是抄風格不是抄旋律")
    ap.add_argument("--style-influence", type=float, default=100.0)
    ap.add_argument("--negative-tags", default=None)
    ap.add_argument("--outdir", default=".", help="成品存哪")
    args = ap.parse_args()

    if not health():
        raise SystemExit(START_HINT)

    lyrics_path = Path(args.lyrics).expanduser().resolve()
    if not lyrics_path.exists():
        raise SystemExit(f"找不到歌詞檔：{lyrics_path}")
    # utf-8-sig：Windows 記事本存 UTF-8 會加 BOM，用 utf-8 讀開頭會多一個看不見的字元
    lyrics = lyrics_path.read_text(encoding="utf-8-sig").strip()
    if not lyrics:
        raise SystemExit("歌詞檔是空的。")
    # 刻意不印內容，只報行數——歌詞有版權，不留在終端機紀錄裡
    print(f"讀到歌詞 {len(lyrics.splitlines())} 行、{len(lyrics)} 字")

    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    for i in range(args.n):
        body = {
            "prompt": args.prompt or args.tags,
            "lyrics": lyrics,
            "tags": args.tags,
            "duration_ms": int(args.duration_sec * 1000),
            "temperature": args.temperature,
            "cfg_scale": args.cfg_scale,
            "style_influence": args.style_influence,
        }
        if args.title:
            body["title"] = args.title
        if args.seed is not None:
            body["seed"] = args.seed + i
        if args.ref_audio_id:
            body["ref_audio_id"] = args.ref_audio_id
        if args.negative_tags:
            body["negative_tags"] = args.negative_tags

        r = requests.post(f"{BASE}/generate/music", json=body, timeout=30)
        r.raise_for_status()
        job_id = r.json()["job_id"]
        print(f"\n[{i+1}/{args.n}] job {job_id}")

        t0 = time.time()
        last = None
        while True:
            time.sleep(5)
            j = requests.get(f"{BASE}/jobs/{job_id}", timeout=15).json()
            st = j.get("status")
            if st != last:
                print(f"    {int(time.time()-t0):4d}s  {st}")
                last = st
            if st == "completed":
                break
            if st == "failed":
                print(f"    失敗：{j.get('error_msg')}")
                break

        if last != "completed":
            continue

        dst = outdir / f"heartmula_{job_id[:8]}.mp3"
        with requests.get(f"{BASE}/download_track/{job_id}", stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(dst, "wb") as f:
                for chunk in resp.iter_content(1 << 16):
                    f.write(chunk)
        print(f"    → {dst}  ({dst.stat().st_size/1e6:.1f} MB, "
              f"{j.get('generation_time_seconds', 0):.0f}s)")

    print("\n挑選建議：同設定多生幾首，先聽副歌和收尾，中文咬字是這個模型最弱的地方。")


if __name__ == "__main__":
    main()
