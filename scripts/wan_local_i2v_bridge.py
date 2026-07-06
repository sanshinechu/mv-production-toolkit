#!/usr/bin/env python
"""Bridge MV_05 scene images and MV_06 prompts to the local Wan 2.1 UI."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


DEFAULT_BASE_URL = "http://127.0.0.1:7860"
DEFAULT_SCENES_DIR = Path(
    r"<雲端硬碟根目錄>\claude code\MV製作\outputs"
    r"\MV_05_快樂學習_九宮格提質拆圖_2026-05-20\scenes-from-4x"
)
DEFAULT_PROMPTS_FILE = Path(
    r"<雲端硬碟根目錄>\claude code\MV製作\outputs"
    r"\MV_06_快樂學習_影片提示詞_2026-05-20.md"
)
DEFAULT_MANIFEST = Path(
    r"<雲端硬碟根目錄>\claude code\MV製作\outputs"
    r"\MV_06_快樂學習_Wan本地影片任務_2026-05-20.json"
)


COMMON_NEGATIVE = (
    "low quality, blurry, distorted face, distorted hands, extra fingers, "
    "changed teacher identity, changed outfit, duplicate teacher, text, "
    "subtitle, watermark, logo, flickering, horror, dark mood"
)


def request_json(url: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        raw = res.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def check_service(base_url: str) -> dict:
    return request_json(f"{base_url}/api/status", timeout=10)


def parse_prompts(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"## Scene\s+(\d{2})\s+-.*?"
        r"來源圖：`([^`]+)`.*?"
        r"影片提示詞：\s*(.*?)\s*"
        r"運鏡建議：\s*(.*?)(?=\n## Scene|\n## 共通負面提示詞|\Z)",
        re.S,
    )
    prompts: dict[str, dict[str, str]] = {}
    for match in pattern.finditer(text):
        scene_no, image_name, prompt, camera = match.groups()
        key = f"scene-{scene_no}"
        prompts[key] = {
            "image_name": image_name.strip(),
            "prompt": " ".join(prompt.split()),
            "camera": " ".join(camera.split()),
        }
    return prompts


def find_scene_images(scenes_dir: Path) -> dict[str, Path]:
    images: dict[str, Path] = {}
    for path in sorted(scenes_dir.glob("scene-*.png")):
        match = re.match(r"(scene-\d{2})-", path.name)
        if match:
            images[match.group(1)] = path
    return images


def upload_image(base_url: str, image_path: Path) -> str:
    boundary = f"----WanBridge{uuid.uuid4().hex}".encode("ascii")
    content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    file_bytes = image_path.read_bytes()
    body = b"".join(
        [
            b"--" + boundary + b"\r\n",
            (
                f'Content-Disposition: form-data; name="image"; '
                f'filename="{image_path.name}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            b"\r\n--" + boundary + b"--\r\n",
        ]
    )
    req = urllib.request.Request(
        f"{base_url}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode('ascii')}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        data = json.loads(res.read().decode("utf-8"))
    return data["filename"]


def submit_i2v(
    base_url: str,
    prompt: str,
    image_name: str,
    negative: str,
    seconds: int,
    fps: int,
    steps: int,
    cfg: float,
    ratio: str,
    resolution: str,
    seed: int | None,
) -> dict:
    payload = {
        "mode": "i2v",
        "prompt": prompt,
        "negative": negative,
        "image": image_name,
        "seconds": seconds,
        "fps": fps,
        "steps": steps,
        "cfg": cfg,
        "ratio": ratio,
        "resolution": resolution,
    }
    if seed:
        payload["seed"] = seed
    return request_json(f"{base_url}/api/generate", payload=payload, timeout=60)


def poll_job(base_url: str, prompt_id: str, interval: int, timeout: int) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = request_json(f"{base_url}/api/job/{urllib.parse.quote(prompt_id)}", timeout=30)
        if data.get("done") or data.get("error"):
            return data
        print(data.get("status", "生成中..."))
        time.sleep(interval)
    return {"done": False, "error": f"等待逾時：{timeout} 秒"}


def choose_scenes(all_scene_keys: list[str], requested: str) -> list[str]:
    if requested == "all":
        return all_scene_keys
    chosen = []
    for part in requested.split(","):
        part = part.strip()
        if not part:
            continue
        if re.fullmatch(r"\d{1,2}", part):
            part = f"scene-{int(part):02d}"
        chosen.append(part)
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description="Send MV_05 scenes to local Wan 2.1 I2V UI.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--scenes-dir", type=Path, default=DEFAULT_SCENES_DIR)
    parser.add_argument("--prompts-file", type=Path, default=DEFAULT_PROMPTS_FILE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--scene", default="1", help="'all', '1', 'scene-01', or comma list.")
    parser.add_argument("--seconds", type=int, default=3)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--cfg", type=float, default=6.0)
    parser.add_argument("--ratio", default="1:1", choices=["16:9", "9:16", "1:1", "4:3", "3:4"])
    parser.add_argument("--resolution", default="低顯存測試", choices=["低顯存測試", "360p", "480p"])
    parser.add_argument("--negative", default=COMMON_NEGATIVE)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--submit", action="store_true", help="Actually submit jobs to local Wan UI.")
    parser.add_argument("--wait", action="store_true", help="Wait for each submitted job to finish.")
    parser.add_argument("--poll-interval", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()

    prompts = parse_prompts(args.prompts_file)
    images = find_scene_images(args.scenes_dir)
    scene_keys = choose_scenes(sorted(set(prompts) & set(images)), args.scene)

    missing = [key for key in scene_keys if key not in prompts or key not in images]
    if missing:
        print(f"找不到這些分鏡資料：{', '.join(missing)}", file=sys.stderr)
        return 2

    manifest = {
        "base_url": args.base_url,
        "scenes_dir": str(args.scenes_dir),
        "prompts_file": str(args.prompts_file),
        "settings": {
            "seconds": args.seconds,
            "fps": args.fps,
            "steps": args.steps,
            "cfg": args.cfg,
            "ratio": args.ratio,
            "resolution": args.resolution,
            "submit": args.submit,
        },
        "jobs": [],
    }
    if args.manifest.exists():
        try:
            existing = json.loads(args.manifest.read_text(encoding="utf-8"))
            if isinstance(existing.get("jobs"), list):
                manifest["jobs"] = existing["jobs"]
        except json.JSONDecodeError:
            pass

    if not args.submit:
        existing_dry_run = {job.get("scene") for job in manifest["jobs"] if job.get("status") == "dry-run"}
        for key in scene_keys:
            if key in existing_dry_run:
                continue
            manifest["jobs"].append(
                {
                    "scene": key,
                    "image": str(images[key]),
                    "prompt": prompts[key]["prompt"],
                    "status": "dry-run",
                }
            )
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已建立 dry-run 任務清單：{args.manifest}")
        print("若要真的送出影片生成，請加上 --submit。")
        return 0

    try:
        status = check_service(args.base_url)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"本地 Wan 服務無法連線：{args.base_url}。請先啟動 START_Wan_中文介面.bat。", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 3
    if not status.get("ok"):
        print(f"Wan UI 可連線，但 ComfyUI 尚未就緒：{status}", file=sys.stderr)
        return 4

    for key in scene_keys:
        image_file = images[key]
        print(f"上傳 {key}: {image_file.name}")
        uploaded = upload_image(args.base_url, image_file)
        print(f"送出 {key} 圖片轉影片")
        response = submit_i2v(
            args.base_url,
            prompts[key]["prompt"],
            uploaded,
            args.negative,
            args.seconds,
            args.fps,
            args.steps,
            args.cfg,
            args.ratio,
            args.resolution,
            args.seed,
        )
        job = {
            "scene": key,
            "image": str(image_file),
            "uploaded_image": uploaded,
            "prompt_id": response.get("prompt_id"),
            "meta": response.get("meta"),
            "status": "submitted",
        }
        if args.wait and job["prompt_id"]:
            result = poll_job(args.base_url, job["prompt_id"], args.poll_interval, args.timeout)
            job["result"] = result
            job["status"] = "done" if result.get("done") else "error"
        manifest["jobs"].append(job)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"任務紀錄已寫入：{args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
