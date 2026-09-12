"""Generate a melody-preserving ACE-Step cover through its public Gradio API."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from gradio_client import Client, handle_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--source-audio", required=True)
    parser.add_argument("--lyrics", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--bpm", type=float, default=123.0)
    parser.add_argument("--key", default="E♭ major")
    parser.add_argument("--cover-strength", type=float, default=0.78)
    parser.add_argument("--seed", type=int, default=20260912)
    args = parser.parse_args()

    source = Path(args.source_audio).expanduser().resolve()
    lyrics_path = Path(args.lyrics).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Source audio not found: {source}")
    if not lyrics_path.is_file():
        raise SystemExit(f"Lyrics file not found: {lyrics_path}")
    outdir.mkdir(parents=True, exist_ok=True)
    lyrics = lyrics_path.read_text(encoding="utf-8-sig").strip()

    values = [
        args.caption, lyrics, args.bpm, args.key, "4/4", "zh", 8, 7.0,
        False, args.seed, None, args.duration, 1, handle_file(str(source)),
        None, 0.0, -1.0,
        "Follow the source melody and timing closely. Sing the supplied Mandarin lyrics with clear diction and controlled emotional growth.",
        1.0, args.cover_strength, False, False, 0.0, 1.0, 3.0, "ode",
        "euler", 0.0, 0.0, True, "double", 0.05, 0.02, "haar", None,
        "mp3", "320k", 48000, 0.85, False, 2.0, 0, 0.9,
        "weak breathy vocal, cute voice, childlike voice, harsh screaming, unclear Mandarin diction, off-key singing",
        True, False, True, False, True, False, False, 0.5, 8,
        "vocals", {}, True, -1.0, 0.0, 0.15, 0.0,
        1.0, "balanced", 0.5, 0.0, None, False, "", "", 0.0, 1.0, 1,
        False,
    ]

    client = Client(args.base_url, verbose=True)
    result = client.predict(*values, api_name="/generation_wrapper")
    first = result[0]
    if not first:
        raise SystemExit(f"ACE-Step returned no audio. Status: {result[10] if len(result) > 10 else 'unknown'}")
    src = Path(first)
    dst = outdir / "至少還有你_爆發女聲_60秒測試_完整生成.mp3"
    shutil.copy2(src, dst)
    payload = {
        "output": str(dst),
        "details": result[9] if len(result) > 9 else "",
        "status": result[10] if len(result) > 10 else "",
        "seed": result[11] if len(result) > 11 else str(args.seed),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
