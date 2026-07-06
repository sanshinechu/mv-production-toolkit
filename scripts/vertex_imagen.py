"""
Vertex AI Imagen 生圖腳本
用法：python vertex_imagen.py "你的提示詞" --output output.png
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

# 金鑰路徑（可透過環境變數覆蓋）
DEFAULT_KEY_PATH = r"I:\我的雲端硬碟\Gemini Gems\glassy-keyword-498400-f7-c38ab260db5f.json"
PROJECT_ID = "gen-lang-client-0086054341"
LOCATION = "us-central1"
MODEL = "imagen-3.0-generate-001"


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
    key_path: str = DEFAULT_KEY_PATH
) -> list[str]:
    import requests

    token = get_access_token(key_path)

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/"
        f"publishers/google/models/{MODEL}:predict"
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
    parser.add_argument("--key", default=DEFAULT_KEY_PATH, help="JSON 金鑰路徑")

    args = parser.parse_args()
    generate_image(args.prompt, args.output, args.ratio, args.count, args.key)
