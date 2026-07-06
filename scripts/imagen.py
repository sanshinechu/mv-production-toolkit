# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Vertex AI Imagen CLI 生圖工具
整合至 MV 製作 Step 7：圖片生成

單張用法：
  python scripts/imagen.py "your prompt here"
  python scripts/imagen.py "your prompt" --count 4 --ratio 16:9 --prefix scene_01

批次用法：
  python scripts/imagen.py --batch scripts/batch_example.yaml
  python scripts/imagen.py --batch my_mv_scenes.yaml --out outputs/scenes

環境變數：
  GOOGLE_APPLICATION_CREDENTIALS  Service Account JSON 路徑
  GOOGLE_CLOUD_PROJECT             GCP Project ID
  GOOGLE_CLOUD_LOCATION            區域（預設 us-central1）
"""

import argparse
import base64
import os
import sys
import time

# Windows 環境強制 UTF-8 輸出，避免 cp950 編碼錯誤
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from datetime import datetime
from pathlib import Path

import google.auth
import google.auth.transport.requests
import requests
import yaml

# 預設值
DEFAULT_PROJECT  = os.environ.get("GOOGLE_CLOUD_PROJECT", "glassy-keyword-498400-f7")
DEFAULT_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
DEFAULT_MODEL    = "imagen-3.0-generate-002"
DEFAULT_OUT      = Path(__file__).parent.parent / "outputs" / "scenes"
VALID_RATIOS     = {"1:1", "16:9", "9:16", "4:3", "3:4"}
RETRY_WAIT       = 65   # 配額限制時等待秒數（1 分鐘）
MAX_RETRIES      = 3


def get_token() -> str:
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def generate(prompt, count, ratio, project, location, model):
    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/"
        f"{project}/locations/{location}/publishers/google/models/{model}:predict"
    )
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": count,
            "aspectRatio": ratio,
            "safetyFilterLevel": "block_some",
            "personGeneration": "allow_adult",
        },
    }

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)

        if resp.status_code == 200:
            return [p["bytesBase64Encoded"] for p in resp.json().get("predictions", [])]

        if resp.status_code == 429:
            # 配額限制 → 等待後重試
            if attempt < MAX_RETRIES:
                print(f"  ⏳ 配額限制，等待 {RETRY_WAIT} 秒後重試（{attempt}/{MAX_RETRIES}）...")
                for remaining in range(RETRY_WAIT, 0, -5):
                    print(f"     還剩 {remaining} 秒...", end="\r")
                    time.sleep(5)
                print()
                continue
            else:
                raise RuntimeError(f"配額限制，已重試 {MAX_RETRIES} 次仍失敗")

        raise RuntimeError(f"API 錯誤 {resp.status_code}: {resp.text}")


def save(images_b64, out_dir, prefix):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []
    for i, b64 in enumerate(images_b64):
        path = out_dir / f"{prefix}_{ts}_{i+1:02d}.png"
        path.write_bytes(base64.b64decode(b64))
        saved.append(path)
    return saved


def run_single(prompt, count, ratio, out, prefix, model, project, location):
    print(f"  比例：{ratio}  張數：{count}")
    print(f"  Prompt：{prompt[:90]}{'...' if len(prompt) > 90 else ''}")
    images = generate(prompt, count, ratio, project, location, model)
    paths = save(images, out, prefix)
    for p in paths:
        print(f"  [OK] {p.name}")
    return paths


def run_batch(batch_file, default_out, default_model, project, location):
    batch_path = Path(batch_file)
    if not batch_path.exists():
        print(f"[錯誤] 找不到批次檔：{batch_file}", file=sys.stderr)
        sys.exit(1)

    with open(batch_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    settings = data.get("settings", {})
    scenes   = data.get("scenes", [])

    if not scenes:
        print("[錯誤] 批次檔中沒有 scenes 項目", file=sys.stderr)
        sys.exit(1)

    global_out    = Path(settings.get("out", default_out))
    global_ratio  = settings.get("ratio", "1:1")
    global_count  = settings.get("count", 1)
    global_model  = settings.get("model", default_model)
    global_prefix = settings.get("prefix", "imagen")

    total     = len(scenes)
    success   = 0
    failed    = []
    all_paths = []

    print(f"\n📋 批次清單：{batch_path.name}（共 {total} 個場景）")
    print(f"{'─' * 55}")

    for idx, scene in enumerate(scenes, 1):
        prompt = scene.get("prompt", "").strip()
        if not prompt:
            print(f"\n[{idx}/{total}] [SKIP] 跳過（沒有 prompt）")
            continue

        ratio  = scene.get("ratio",  global_ratio)
        count  = scene.get("count",  global_count)
        out    = Path(scene.get("out", global_out))
        prefix = scene.get("prefix", f"{global_prefix}_{idx:02d}")
        model  = scene.get("model",  global_model)
        name   = scene.get("name",   f"場景 {idx}")

        print(f"\n[{idx}/{total}] {name}")

        try:
            t0 = time.time()
            paths = run_single(prompt, count, ratio, out, prefix, model, project, location)
            elapsed = time.time() - t0
            print(f"  ⏱  {elapsed:.1f} 秒")
            all_paths.extend(paths)
            success += 1
        except Exception as e:
            print(f"  [FAIL] 失敗：{e}")
            failed.append(name)

        # 場景間稍停，避免打太快
        if idx < total:
            time.sleep(2)

    print(f"\n{'═' * 55}")
    print(f"  批次完成：{success}/{total} 成功，{len(failed)} 失敗")
    if failed:
        print(f"  失敗場景：{', '.join(failed)}")
    print(f"  共生成圖片：{len(all_paths)} 張")
    print(f"{'═' * 55}")

    return all_paths


def main():
    parser = argparse.ArgumentParser(
        description="Vertex AI Imagen CLI - MV Step 7（支援單張與批次生圖）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 單張
  python scripts/imagen.py "A woman in coffee shop, cinematic"
  python scripts/imagen.py "Tokyo night" --count 4 --ratio 16:9 --prefix scene_01

  # 批次（讀取 YAML 清單）
  python scripts/imagen.py --batch scripts/batch_example.yaml
        """,
    )

    parser.add_argument("prompt", nargs="?", help="圖片描述（單張模式）")
    parser.add_argument("--count",    type=int, default=1, choices=range(1, 5), metavar="1-4")
    parser.add_argument("--ratio",    default="1:1", choices=sorted(VALID_RATIOS))
    parser.add_argument("--out",      type=Path, default=DEFAULT_OUT)
    parser.add_argument("--prefix",   default="imagen")
    parser.add_argument("--batch",    help="批次 YAML 檔路徑")
    parser.add_argument("--model",    default=DEFAULT_MODEL)
    parser.add_argument("--project",  default=DEFAULT_PROJECT)
    parser.add_argument("--location", default=DEFAULT_LOCATION)

    args = parser.parse_args()

    print("=" * 55)
    print("  Vertex AI Imagen - MV 製作 Step 7")
    print("=" * 55)

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if creds_path:
        print(f"  憑證：{Path(creds_path).name}")
    print(f"  模型：{args.model}")

    if args.batch:
        run_batch(args.batch, args.out, args.model, args.project, args.location)

    elif args.prompt:
        print(f"\n生圖中...")
        try:
            paths = run_single(
                prompt=args.prompt,
                count=args.count,
                ratio=args.ratio,
                out=args.out,
                prefix=args.prefix,
                model=args.model,
                project=args.project,
                location=args.location,
            )
            print(f"\n📁 輸出位置：{args.out.resolve()}")
            print(f"🎨 本次生成：{len(paths)} 張")
        except Exception as e:
            print(f"[錯誤] {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
