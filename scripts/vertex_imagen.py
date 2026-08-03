"""
Vertex AI Imagen 生圖腳本
用法：python vertex_imagen.py "你的提示詞" --output output.png

設定（讀取順序：命令列參數 → 環境變數 → ./.env → ~/.vertexai.env）：
  GOOGLE_APPLICATION_CREDENTIALS  服務帳戶 JSON 路徑
  GOOGLE_CLOUD_PROJECT            Vertex 專案 ID
  GOOGLE_CLOUD_LOCATION           區域，預設 us-central1
  VERTEX_IMAGEN_MODEL             模型，預設 imagen-3.0-generate-001

金鑰路徑與專案 ID 不寫死在原始碼裡（這個 repo 是公開的）。
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

DEFAULT_LOCATION = "us-central1"
DEFAULT_MODEL = "imagen-3.0-generate-001"


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


def resolve_config(
    key_path: str | None, project: str | None, location: str | None = None
) -> tuple[str, str, str, str]:
    """金鑰路徑與專案一律從參數或環境變數拿，不寫死在原始碼裡。"""
    load_env()
    key_path = key_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = location or os.environ.get("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION)
    if location == "global":
        # ~/.vertexai.env 為了 gemini-3.1-flash-image 設成 global，但 Imagen 的 predict
        # 端點不開在 global，照用會直接 404。這裡自動退回 us-central1。
        print(f"[warn] GOOGLE_CLOUD_LOCATION=global 不支援 Imagen predict，改用 {DEFAULT_LOCATION}")
        location = DEFAULT_LOCATION
    model = os.environ.get("VERTEX_IMAGEN_MODEL", DEFAULT_MODEL)

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
            "  GOOGLE_CLOUD_LOCATION=us-central1\n"
            "  GOOGLE_APPLICATION_CREDENTIALS=金鑰JSON的完整路徑\n"
            "也可以用 --key / --project 直接指定。"
        )
    if not Path(key_path).exists():
        sys.exit(f"找不到服務帳戶金鑰：{key_path}")
    return key_path, project, location, model


def get_access_token(key_path: str) -> str:
    from google.oauth2 import service_account
    import google.auth.transport.requests

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def generate_image(
    prompt: str,
    output_path: str = "output.png",
    aspect_ratio: str = "1:1",
    sample_count: int = 1,
    key_path: str | None = None,
    project: str | None = None,
    location: str | None = None,
) -> list[str]:
    import requests

    key_path, project, location, model = resolve_config(key_path, project, location)
    token = get_access_token(key_path)

    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{location}/"
        f"publishers/google/models/{model}:predict"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": sample_count,
            "aspectRatio": aspect_ratio,
        }
    }

    print(f"[Imagen] 生成中：{prompt[:60]}...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"[ERROR] {response.status_code}: {response.text}")
        sys.exit(1)

    predictions = response.json().get("predictions", [])
    saved_files = []

    for i, pred in enumerate(predictions):
        image_data = base64.b64decode(pred["bytesBase64Encoded"])
        if sample_count > 1:
            path = Path(output_path)
            out = path.parent / f"{path.stem}_{i+1}{path.suffix}"
        else:
            out = Path(output_path)

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(image_data)
        saved_files.append(str(out))
        print(f"[OK] 已儲存：{out}")

    return saved_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vertex AI Imagen 生圖")
    parser.add_argument("prompt", help="圖片提示詞（英文效果最好）")
    parser.add_argument("--output", "-o", default="output.png", help="輸出檔案路徑")
    parser.add_argument("--ratio", "-r", default="1:1",
                        choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
                        help="畫面比例（預設 1:1）")
    parser.add_argument("--count", "-n", type=int, default=1, help="生成張數（1-4）")
    parser.add_argument("--key", help="JSON 金鑰路徑（預設讀 GOOGLE_APPLICATION_CREDENTIALS）")
    parser.add_argument("--project", help="Vertex 專案 ID（預設讀 GOOGLE_CLOUD_PROJECT）")
    parser.add_argument("--location", help=f"區域（預設讀 GOOGLE_CLOUD_LOCATION，再預設 {DEFAULT_LOCATION}）")

    args = parser.parse_args()
    generate_image(
        args.prompt, args.output, args.ratio, args.count, args.key, args.project, args.location
    )
