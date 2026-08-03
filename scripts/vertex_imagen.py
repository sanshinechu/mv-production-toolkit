"""
Vertex AI 生圖腳本（Gemini 3.1 Flash Image）
用法：python vertex_imagen.py "你的提示詞" --output output.png

歷史說明：本檔原本走 Imagen 的 predict 端點（`imagen-3.0-generate-001`），
該模型已停用，Vertex 會回 404 `Publisher model ... was not found`。
內部改用 Gemini 的 generate_content()，核心邏輯沿用剪片工作流已驗證過的 draw_gemini.py。
**檔名與命令列參數維持不變**，舊工作流不用改。

設定（讀取順序：命令列參數 → 環境變數 → ./.env → ~/.vertexai.env）：
  GOOGLE_APPLICATION_CREDENTIALS  服務帳戶 JSON 路徑
  GOOGLE_CLOUD_PROJECT            Vertex 專案 ID
  GOOGLE_CLOUD_LOCATION           區域，預設 global（Gemini 影像模型只開在 global）
  VERTEX_IMAGE_MODEL              模型，預設 gemini-3.1-flash-image
                                  （舊名 VERTEX_IMAGEN_MODEL 仍可用，但已棄用）

金鑰路徑與專案 ID 不寫死在原始碼裡（這個 repo 是公開的）。

需要套件：google-genai
  uv run --with google-genai python scripts/vertex_imagen.py "..." --check
"""

import argparse
import os
import sys
from pathlib import Path

DEFAULT_LOCATION = "global"
DEFAULT_MODEL = "gemini-3.1-flash-image"
DEFAULT_IMAGE_SIZE = "1K"
QUALITY_IMAGE_SIZE = "2K"
SUPPORTED_ASPECTS = ["1:1", "16:9", "9:16", "4:3", "3:4"]
RETIRED_MODELS = ("imagen-3.0", "imagen-4.0")


def load_env_from_file(path: Path) -> None:
    """讀 .env 格式，不覆蓋已存在的環境變數。"""
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_env() -> None:
    load_env_from_file(Path.cwd() / ".env")
    load_env_from_file(Path.home() / ".vertexai.env")


def resolve_model() -> str:
    """新名稱優先；舊名稱還能用，但會提醒。"""
    model = os.environ.get("VERTEX_IMAGE_MODEL")
    if model:
        return model
    legacy = os.environ.get("VERTEX_IMAGEN_MODEL")
    if legacy:
        print("[warn] VERTEX_IMAGEN_MODEL 已棄用，請改用 VERTEX_IMAGE_MODEL", file=sys.stderr)
        return legacy
    return DEFAULT_MODEL


def resolve_config(
    key_path: str | None = None,
    project: str | None = None,
    location: str | None = None,
    model: str | None = None,
) -> dict:
    """金鑰路徑與專案一律從參數或環境變數拿，不寫死在原始碼裡。"""
    load_env()
    key_path = key_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or DEFAULT_LOCATION
    model = model or resolve_model()

    missing = []
    if not key_path:
        missing.append("GOOGLE_APPLICATION_CREDENTIALS（服務帳戶 JSON 路徑）")
    if not project:
        missing.append("GOOGLE_CLOUD_PROJECT（Vertex 專案 ID）")
    if missing:
        sys.exit(
            "缺少設定：" + "、".join(missing) + "\n"
            "請在 ~/.vertexai.env 或環境變數裡設好，例如：\n"
            "  GOOGLE_CLOUD_PROJECT=你的專案ID\n"
            "  GOOGLE_CLOUD_LOCATION=global\n"
            "  GOOGLE_APPLICATION_CREDENTIALS=金鑰JSON的完整路徑\n"
            "也可以用 --key / --project 直接指定。"
        )
    if not Path(key_path).exists():
        sys.exit(f"找不到服務帳戶金鑰：{key_path}")
    if location != DEFAULT_LOCATION:
        print(
            f"[warn] GOOGLE_CLOUD_LOCATION={location}，但 Gemini 影像模型只開在 "
            f"{DEFAULT_LOCATION}，其他區域會回 404",
            file=sys.stderr,
        )
    if model.startswith(RETIRED_MODELS):
        print(f"[warn] {model} 屬於已停用的 Imagen 端點，Vertex 會回 404", file=sys.stderr)

    # SDK 靠這個環境變數找服務帳戶；用 --key 指定時要補回去
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    return {"key_path": key_path, "project": project, "location": location, "model": model}


def build_client(project: str, location: str):
    from google import genai

    return genai.Client(vertexai=True, project=project, location=location)


def build_generate_config(image_config):
    """把 SDK 型別的組裝集中在這裡，render() 本身就不必 import google.genai，
    離線測試才有辦法在沒裝套件的機器上跑。"""
    from google.genai import types

    return types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=image_config)


def build_image_config(aspect: str, image_size: str):
    """組 ImageConfig；舊版 SDK 不支援 image_size 時自動退回只設長寬比。"""
    from google.genai import types

    try:
        return types.ImageConfig(aspect_ratio=aspect, image_size=image_size)
    except TypeError:
        return types.ImageConfig(aspect_ratio=aspect)


def output_paths(output_path: str, sample_count: int) -> list[Path]:
    """維持原本的輸出命名：單張就是 --output，多張才加 _1、_2…"""
    path = Path(output_path)
    if sample_count == 1:
        return [path]
    return [path.parent / f"{path.stem}_{i + 1}{path.suffix}" for i in range(sample_count)]


def render(
    prompt: str,
    targets: list[Path],
    aspect_ratio: str = "1:1",
    image_size: str = DEFAULT_IMAGE_SIZE,
    key_path: str | None = None,
    project: str | None = None,
    location: str | None = None,
    model: str | None = None,
) -> list[Path]:
    """唯一會呼叫 Gemini 的地方。要幾張就給幾個目標路徑。

    其他腳本（例如 imagen.py 的批次模式）一律走這裡，不要各自再寫一份 API 邏輯。
    """
    if aspect_ratio not in SUPPORTED_ASPECTS:
        sys.exit(f"不支援的長寬比 {aspect_ratio}。可用：{', '.join(SUPPORTED_ASPECTS)}")

    cfg = resolve_config(key_path, project, location, model)
    client = build_client(cfg["project"], cfg["location"])
    image_config = build_image_config(aspect_ratio, image_size)
    saved: list[Path] = []

    print(f"[Gemini] {cfg['model']} 生成中：{prompt[:60]}...（{aspect_ratio}, {image_size}）")

    # Gemini 影像模型一次只回一張，靠迴圈跑滿張數。
    for out in targets:
        response = client.models.generate_content(
            model=cfg["model"],
            contents=prompt,
            config=build_generate_config(image_config),
        )

        image = None
        for part in response.parts:
            image = part.as_image()
            if image is not None:
                break
        if image is None:
            sys.exit(
                "回應沒有夾帶圖片。可能是 prompt 被安全機制擋下，"
                "或這個專案還沒開通 gemini-3.1-flash-image。"
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(out))
        saved.append(out)
        print(f"[OK] 已儲存：{out}")

    return saved


def timestamped_paths(out_dir, prefix: str, count: int) -> list[Path]:
    """批次模式的命名慣例：<prefix>_<時間戳>_01.png"""
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return [Path(out_dir) / f"{prefix}_{stamp}_{i + 1:02d}.png" for i in range(count)]


def generate_to_dir(
    prompt: str,
    out_dir,
    prefix: str = "image",
    count: int = 1,
    aspect_ratio: str = "1:1",
    image_size: str = DEFAULT_IMAGE_SIZE,
    key_path: str | None = None,
    project: str | None = None,
    location: str | None = None,
    model: str | None = None,
) -> list[Path]:
    """存進資料夾、檔名自動加時間戳；給 imagen.py 這類批次工具用。"""
    return render(
        prompt,
        timestamped_paths(out_dir, prefix, count),
        aspect_ratio,
        image_size,
        key_path,
        project,
        location,
        model,
    )


def generate_image(
    prompt: str,
    output_path: str = "output.png",
    aspect_ratio: str = "1:1",
    sample_count: int = 1,
    key_path: str | None = None,
    project: str | None = None,
    location: str | None = None,
    image_size: str = DEFAULT_IMAGE_SIZE,
) -> list[str]:
    """單張／指定檔名的入口，維持原本的 CLI 行為。"""
    saved = render(
        prompt,
        output_paths(output_path, sample_count),
        aspect_ratio,
        image_size,
        key_path,
        project,
        location,
    )
    return [str(p) for p in saved]


def check_config(args) -> None:
    """只驗設定與參數解析，不呼叫 API、不生圖。"""
    cfg = resolve_config(args.key, args.project, args.location)
    print("─" * 56)
    print(f"專案　：{cfg['project']}")
    print(f"區域　：{cfg['location']}")
    print(f"模型　：{cfg['model']}")
    print(f"金鑰　：{cfg['key_path']}")
    print(f"比例　：{args.ratio}（支援 {', '.join(SUPPORTED_ASPECTS)}）")
    print(f"張數　：{args.count}")
    print(f"輸出　：{'、'.join(str(p) for p in output_paths(args.output, args.count))}")
    print("─" * 56)
    print("[check] 設定完整，沒有呼叫 API。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vertex AI 生圖（Gemini 3.1 Flash Image）")
    parser.add_argument("prompt", nargs="?", default="", help="圖片提示詞（英文效果最好）")
    parser.add_argument("--output", "-o", default="output.png", help="輸出檔案路徑")
    parser.add_argument("--ratio", "-r", default="1:1", choices=SUPPORTED_ASPECTS,
                        help="畫面比例（預設 1:1）")
    parser.add_argument("--count", "-n", type=int, default=1, help="生成張數（1-4）")
    parser.add_argument("--key", help="JSON 金鑰路徑（預設讀 GOOGLE_APPLICATION_CREDENTIALS）")
    parser.add_argument("--project", help="Vertex 專案 ID（預設讀 GOOGLE_CLOUD_PROJECT）")
    parser.add_argument("--location", help=f"區域（預設 {DEFAULT_LOCATION}）")
    parser.add_argument("--quality", action="store_true", help="出 2K（預設 1K）")
    parser.add_argument("--check", action="store_true", help="只驗設定與參數，不生圖")

    args = parser.parse_args()

    if args.check:
        check_config(args)
        sys.exit(0)
    if not args.prompt:
        parser.error("需要提示詞（或用 --check 只驗設定）")

    generate_image(
        args.prompt,
        args.output,
        args.ratio,
        args.count,
        args.key,
        args.project,
        args.location,
        QUALITY_IMAGE_SIZE if args.quality else DEFAULT_IMAGE_SIZE,
    )
