"""Generate a melody-preserving ACE-Step cover through its public Gradio API."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from gradio_client import Client, handle_file

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def find_path(value):
    if isinstance(value, (str, Path)):
        return str(value)
    if isinstance(value, dict):
        for key in ("path", "url", "value", "data"):
            if key in value:
                found = find_path(value[key])
                if found:
                    return found
        for child in value.values():
            found = find_path(child)
            if found:
                return found
    if isinstance(value, (list, tuple)):
        for child in value:
            found = find_path(child)
            if found:
                return found
    return None


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
    parser.add_argument("--output-name", default="ace_step_cover.mp3")
    parser.add_argument("--mode", choices=("Custom", "Remix", "Repaint"), default="Remix")
    parser.add_argument("--checkpoint")
    parser.add_argument("--initialize", action="store_true")
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
    if args.initialize:
        if not args.checkpoint:
            raise SystemExit("--checkpoint is required with --initialize")
        init_result = client.predict(
            args.checkpoint,
            "acestep-v15-turbo",
            "auto",
            True,
            "acestep-5Hz-lm-1.7B",
            "pt",
            False,
            True,
            True,
            False,
            True,
            False,
            "Custom",
            1,
            "official",
            api_name="/lambda_6",
        )
        print(f"Initialization: {init_result[0]}", file=sys.stderr)
    mode_result = client.predict(args.mode, api_name="/_handle_mode_change")
    print(f"Mode: {mode_result[2] if len(mode_result) > 2 else args.mode}", file=sys.stderr)
    result = client.predict(*values, api_name="/generation_wrapper")
    first = result[0]
    if not first:
        raise SystemExit(f"ACE-Step returned no audio. Status: {result[10] if len(result) > 10 else 'unknown'}")
    first = find_path(first)
    if not first:
        raise SystemExit("ACE-Step returned an audio object without a usable path")
    src = Path(first)
    dst = outdir / args.output_name
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
