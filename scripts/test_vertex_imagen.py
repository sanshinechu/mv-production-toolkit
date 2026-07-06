#!/usr/bin/env python3
"""
Vertex AI Imagen 生圖 API 測試腳本
使用 Service Account JSON 憑證取得 Bearer token
"""

import requests
import base64
import os
from datetime import datetime

import google.auth
import google.auth.transport.requests

# ── 設定區（從環境變數讀取，也可直接填寫） ───────────────
PROJECT_ID  = os.environ.get("GOOGLE_CLOUD_PROJECT",  "glassy-keyword-498400-f7")
LOCATION    = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
MODEL       = "imagen-3.0-generate-002"  # Imagen 3 正式版
OUTPUT_DIR  = r"I:\我的雲端硬碟\Ai Code\01_MV製作\outputs\vertex_test"
# ─────────────────────────────────────────────────────────


def get_access_token() -> str:
    """透過 Service Account JSON 取得 Bearer token"""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token


def generate_image(prompt: str, count: int = 1) -> list:
    """呼叫 Vertex AI Imagen API 生成圖片，回傳 base64 清單"""
    token = get_access_token()

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/"
        f"{PROJECT_ID}/locations/{LOCATION}/publishers/google/"
        f"models/{MODEL}:predict"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": count,
            "aspectRatio": "1:1",
            "safetyFilterLevel": "block_some",
            "personGeneration": "allow_adult",
        }
    }

    print(f"\n📡 送出請求...")
    print(f"🔗 URL: {url}")
    print(f"🎨 Prompt: {prompt[:80]}...")

    response = requests.post(url, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        print(f"❌ 錯誤 {response.status_code}:")
        print(response.text)
        response.raise_for_status()

    data = response.json()
    images_b64 = [
        pred["bytesBase64Encoded"]
        for pred in data.get("predictions", [])
    ]
    return images_b64


def save_images(images_b64: list, prefix: str = "test") -> list:
    """將 base64 圖片存檔，回傳檔案路徑清單"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []

    for i, b64 in enumerate(images_b64):
        filename = f"{prefix}_{timestamp}_{i+1:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"✅ 已存檔: {filepath}")
        saved.append(filepath)

    return saved


def main():
    prompt = (
        "A young East Asian woman sitting in a cozy coffee shop, "
        "soft natural window light, warm tones, cinematic style, "
        "shallow depth of field, 85mm portrait photography"
    )

    print("🚀 Vertex AI Imagen 生圖測試")
    print("=" * 50)
    print(f"📦 Project:     {PROJECT_ID}")
    print(f"🌍 Location:    {LOCATION}")
    print(f"🤖 Model:       {MODEL}")
    print(f"🔑 Credentials: {CREDENTIALS or '(使用預設憑證)'}")

    # 取得 token 驗證憑證
    try:
        token = get_access_token()
        print(f"🔑 Token 取得成功（前 20 碼）: {token[:20]}...")
    except Exception as e:
        print(f"❌ 取得 token 失敗: {e}")
        print("請確認 GOOGLE_APPLICATION_CREDENTIALS 路徑正確")
        return

    # 生成圖片
    images = generate_image(prompt, count=1)
    print(f"\n🎉 成功生成 {len(images)} 張圖片")

    # 存檔
    paths = save_images(images, prefix="vertex_imagen_test")
    print(f"\n📁 圖片存放位置: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
