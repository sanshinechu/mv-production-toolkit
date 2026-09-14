"""Transcribe a separated singing stem with word timestamps for alignment analysis."""

import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio")
    parser.add_argument("--lyrics")
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="small")
    args = parser.parse_args()

    prompt = None
    if args.lyrics:
        prompt = Path(args.lyrics).read_text(encoding="utf-8-sig")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        args.audio,
        language="zh",
        initial_prompt=prompt,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=True,
    )
    rows = []
    for segment in segments:
        words = []
        for word in segment.words or []:
            words.append({"start": word.start, "end": word.end, "word": word.word})
        rows.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "words": words,
        })
    payload = {
        "language": info.language,
        "language_probability": info.language_probability,
        "segments": rows,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"segments={len(rows)} out={args.out}")


if __name__ == "__main__":
    main()
