# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Vertex AI CLI 生圖工具（Gemini 3.1 Flash Image）
整合至 MV 製作 Step 7：圖片生成

單張用法：
  python scripts/imagen.py "your prompt here"
  python scripts/imagen.py "your prompt" --count 4 --ratio 16:9 --prefix scene_01

批次用法：
  python scripts/imagen.py --batch scripts/batch_example.yaml
  python scripts/imagen.py --batch my_mv_scenes.yaml --out outputs/scenes

生圖邏輯不寫在這裡：一律呼叫 vertex_imagen.render()／generate_to_dir()。
本檔只負責參數整理、YAML 批次迴圈、重試與統計。

環境變數（實際解析在 vertex_imagen.py）：
  GOOGLE_APPLICATION_CREDENTIALS  Service Account JSON 路徑
  GOOGLE_CLOUD_PROJECT            GCP Project ID
  GOOGLE_CLOUD_LOCATION           區域（預設 global）
  VERTEX_IMAGE_MODEL              模型（預設 gemini-3.1-flash-image）
"""

import argparse
import sys
import time

# Windows 環境強制 UTF-8 輸出，避免 cp950 編碼錯誤
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vertex_imagen as vi  # noqa: E402

# 預設值
DEFAULT_OUT  = Path(__file__).parent.parent / "outputs" / "scenes"
VALID_RATIOS = set(vi.SUPPORTED_ASPECTS)
RETRY_WAIT   = 65   # 配額限制時等待秒數（1 分鐘）
MAX_RETRIES  = 3


def is_quota_error(err: Exception) -> bool:
    text = str(err)
    return "429" in text or "RESOURCE_EXHAUSTED" in text or "quota" in text.lower()


def run_single(prompt, count, ratio, out, prefix, model, project, location, image_size=None):
    """單一場景：整理參數 + 配額重試，實際生圖交給 vertex_imagen。"""
    print(f"  比例：{ratio}  張數：{count}")
    print(f"  Prompt：{prompt[:90]}{'...' if len(prompt) > 90 else ''}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            paths = vi.generate_to_dir(
                prompt=prompt,
                out_dir=out,
                prefix=prefix,
                count=count,
                aspect_ratio=ratio,
                image_size=image_size or vi.DEFAULT_IMAGE_SIZE,
                project=project,
                location=location,
                model=model,
            )
            for p in paths:
                print(f"  [OK] {p.name}")
            return paths
        except Exception as e:
            if not is_quota_error(e) or attempt == MAX_RETRIES:
                raise
            print(f"  ⏳ 配額限制，等待 {RETRY_WAIT} 秒後重試（{attempt}/{MAX_RETRIES}）...")
            for remaining in range(RETRY_WAIT, 0, -5):
                print(f"     還剩 {remaining} 秒...", end="\r")
                time.sleep(5)
            print()
    raise RuntimeError(f"配額限制，已重試 {MAX_RETRIES} 次仍失敗")


def run_batch(batch_file, default_out, default_model, project, location, image_size=None):
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
            paths = run_single(
                prompt, count, ratio, out, prefix, model, project, location, image_size
            )
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
        description="Vertex AI 生圖 CLI - MV Step 7（支援單張與批次生圖）",
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
    parser.add_argument("--model",    help=f"模型（預設 {vi.DEFAULT_MODEL}）")
    parser.add_argument("--project",  help="Vertex 專案 ID（預設讀 GOOGLE_CLOUD_PROJECT）")
    parser.add_argument("--location", help=f"區域（預設 {vi.DEFAULT_LOCATION}）")
    parser.add_argument("--quality",  action="store_true", help="出 2K（預設 1K）")
    parser.add_argument("--check",    action="store_true", help="只驗設定與參數，不生圖")

    args = parser.parse_args()

    print("=" * 55)
    print("  Vertex AI 生圖 - MV 製作 Step 7")
    print("=" * 55)

    cfg = vi.resolve_config(None, args.project, args.location, args.model)
    print(f"  憑證：{Path(cfg['key_path']).name}")
    print(f"  專案：{cfg['project']}")
    print(f"  區域：{cfg['location']}")
    print(f"  模型：{cfg['model']}")

    if args.check:
        print("\n[check] 設定完整，沒有呼叫 API。")
        return

    image_size = vi.QUALITY_IMAGE_SIZE if args.quality else vi.DEFAULT_IMAGE_SIZE

    if args.batch:
        run_batch(args.batch, args.out, args.model, args.project, args.location, image_size)

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
                image_size=image_size,
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
