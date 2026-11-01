#!/usr/bin/env python3
"""
Dreamina (Seedance 2.0) 影片生成腳本
透過 fal.ai API 生成影片並下載到本機。

使用方式：
    python generate_video.py \
        --prompt "A cat runs on the beach at sunset" \
        --duration 5 \
        --resolution 720p \
        --aspect_ratio 16:9 \
        --model seedance-2.0 \
        --output ./videos/
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("❌ 需要安裝 requests 套件：pip install requests", file=sys.stderr)
    sys.exit(1)


# --- 模型對應表 -----------------------------------------------------------
MODELS = {
    "seedance-2.0": "bytedance/seedance-2.0/text-to-video",
    "seedance-2.0-fast": "bytedance/seedance-2.0/fast/text-to-video",
    # 舊版備援（若帳戶沒權限用 Seedance 2.0）
    "seedance-1.0-pro-fast": "fal-ai/bytedance/seedance/v1/pro/fast/text-to-video",
}

FAL_BASE = "https://fal.run"
FAL_QUEUE_BASE = "https://queue.fal.run"


def log(msg: str, level: str = "info") -> None:
    """結構化輸出，方便 Claude 解析。"""
    prefix = {"info": "ℹ️ ", "ok": "✅ ", "warn": "⚠️ ", "err": "❌ "}.get(level, "")
    print(f"{prefix}{msg}", flush=True)


def check_api_key() -> str:
    """檢查並回傳 FAL_KEY。"""
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        log("未設定 FAL_KEY 環境變數", "err")
        log("請到 https://fal.ai/dashboard/keys 申請，然後設定：", "info")
        log("  Linux/macOS:  export FAL_KEY='你的key'", "info")
        log("  Windows PS :  $env:FAL_KEY='你的key'", "info")
        sys.exit(2)
    return key


def submit_job(model_path: str, payload: dict, api_key: str) -> str:
    """
    送出非同步 job，回傳 request_id。
    使用 queue endpoint，可以輪詢狀態。
    """
    url = f"{FAL_QUEUE_BASE}/{model_path}"
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }
    log(f"送出請求到 {url}", "info")

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as e:
        log(f"網路錯誤：{e}", "err")
        sys.exit(3)

    if resp.status_code == 401:
        log("FAL_KEY 無效或已失效，請重新確認。", "err")
        sys.exit(4)
    if resp.status_code == 402:
        log("fal.ai 帳戶餘額不足，請至 dashboard 儲值。", "err")
        sys.exit(5)
    if resp.status_code == 422:
        log(f"參數驗證失敗：{resp.text}", "err")
        sys.exit(6)
    if resp.status_code == 429:
        log("請求過於頻繁，請稍後再試。", "err")
        sys.exit(7)
    if not resp.ok:
        log(f"API 錯誤 {resp.status_code}：{resp.text}", "err")
        sys.exit(8)

    data = resp.json()
    request_id = data.get("request_id")
    if not request_id:
        log(f"回應缺少 request_id：{data}", "err")
        sys.exit(9)

    log(f"任務已送出，request_id = {request_id}", "ok")
    return request_id


def poll_status(model_path: str, request_id: str, api_key: str,
                max_wait: int = 600) -> dict:
    """輪詢任務狀態直到完成。"""
    url = f"{FAL_QUEUE_BASE}/{model_path}/requests/{request_id}/status"
    result_url = f"{FAL_QUEUE_BASE}/{model_path}/requests/{request_id}"
    headers = {"Authorization": f"Key {api_key}"}

    start = time.time()
    last_status = None

    while time.time() - start < max_wait:
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            log(f"輪詢失敗（會重試）：{e}", "warn")
            time.sleep(5)
            continue

        status = resp.json().get("status", "UNKNOWN")

        if status != last_status:
            log(f"狀態：{status}", "info")
            last_status = status

        if status == "COMPLETED":
            # 拿最終結果
            r = requests.get(result_url, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()
        if status in ("FAILED", "CANCELLED"):
            log(f"任務失敗：{resp.text}", "err")
            sys.exit(10)

        time.sleep(5)

    log(f"等待超過 {max_wait} 秒，放棄輪詢。", "err")
    sys.exit(11)


def download_video(video_url: str, output_dir: Path, prompt_hint: str) -> Path:
    """下載影片到本機，回傳檔案路徑。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 用時間戳 + prompt 前幾個字當檔名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_hint = "".join(c for c in prompt_hint[:30] if c.isalnum() or c in "-_")
    filename = f"dreamina_{timestamp}_{safe_hint}.mp4"
    filepath = output_dir / filename

    log(f"下載影片：{video_url}", "info")
    try:
        with requests.get(video_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.RequestException as e:
        log(f"下載失敗：{e}", "err")
        sys.exit(12)

    size_mb = filepath.stat().st_size / (1024 * 1024)
    log(f"儲存到：{filepath}（{size_mb:.1f} MB）", "ok")
    return filepath


def estimate_cost(resolution: str, duration: int, model: str) -> float:
    """粗略估算費用（USD），只供參考。"""
    rates = {
        ("seedance-2.0", "720p"): 0.3034,
        ("seedance-2.0", "1080p"): 0.60,  # 約估
        ("seedance-2.0-fast", "720p"): 0.15,
        ("seedance-2.0-fast", "1080p"): 0.30,
        ("seedance-1.0-pro-fast", "1080p"): 0.049,
    }
    rate = rates.get((model, resolution), 0.30)
    return rate * duration


def main():
    parser = argparse.ArgumentParser(
        description="用 ByteDance Dreamina (Seedance 2.0) 生成影片"
    )
    parser.add_argument("--prompt", required=True, help="英文提示詞")
    parser.add_argument("--duration", type=int, default=5,
                        choices=[5, 8, 10, 15], help="影片長度（秒）")
    parser.add_argument("--resolution", default="720p",
                        choices=["720p", "1080p"], help="解析度")
    parser.add_argument("--aspect_ratio", default="16:9",
                        choices=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "auto"],
                        help="畫面比例")
    parser.add_argument("--model", default="seedance-2.0",
                        choices=list(MODELS.keys()), help="模型版本")
    parser.add_argument("--generate_audio", action="store_true",
                        help="是否生成音效（會增加費用）")
    parser.add_argument("--seed", type=int, default=None,
                        help="隨機種子（可重現結果）")
    parser.add_argument("--output", default="./videos",
                        help="影片輸出資料夾")
    parser.add_argument("--dry_run", action="store_true",
                        help="只顯示參數不實際呼叫 API")

    args = parser.parse_args()

    # --- Step 1：顯示計畫 -----------------------------------------------
    cost = estimate_cost(args.resolution, args.duration, args.model)
    log("=" * 50, "info")
    log("📋 生成計畫", "info")
    log(f"  模型：{args.model}", "info")
    log(f"  解析度：{args.resolution}", "info")
    log(f"  長度：{args.duration} 秒", "info")
    log(f"  比例：{args.aspect_ratio}", "info")
    log(f"  音效：{'開' if args.generate_audio else '關'}", "info")
    log(f"  預估費用：約 ${cost:.2f} USD", "info")
    log(f"  Prompt：{args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}", "info")
    log("=" * 50, "info")

    if args.dry_run:
        log("Dry run 模式，不實際呼叫 API。", "warn")
        return

    # --- Step 2：檢查 API Key ---------------------------------------------
    api_key = check_api_key()

    # --- Step 3：組 payload -----------------------------------------------
    model_path = MODELS[args.model]
    payload = {
        "prompt": args.prompt,
        "duration": str(args.duration),
        "resolution": args.resolution,
        "aspect_ratio": args.aspect_ratio,
    }
    if args.generate_audio:
        payload["generate_audio"] = True
    if args.seed is not None:
        payload["seed"] = args.seed

    # --- Step 4：送出並輪詢 -----------------------------------------------
    request_id = submit_job(model_path, payload, api_key)
    result = poll_status(model_path, request_id, api_key)

    # --- Step 5：下載 -----------------------------------------------------
    video_info = result.get("video") or {}
    video_url = video_info.get("url")
    if not video_url:
        log(f"回應中沒有影片 URL：{json.dumps(result, indent=2)}", "err")
        sys.exit(13)

    output_dir = Path(args.output)
    filepath = download_video(video_url, output_dir, args.prompt)

    # --- Step 6：總結 -----------------------------------------------------
    log("=" * 50, "ok")
    log("🎉 影片生成完成！", "ok")
    log(f"  檔案：{filepath}", "ok")
    log(f"  實際費用：約 ${cost:.2f} USD（以 fal.ai 帳單為準）", "ok")
    if result.get("seed"):
        log(f"  Seed：{result['seed']}（可用來重現類似結果）", "info")
    log("=" * 50, "ok")


if __name__ == "__main__":
    main()
