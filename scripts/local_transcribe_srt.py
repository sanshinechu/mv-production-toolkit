import argparse
from pathlib import Path

from faster_whisper import WhisperModel
from faster_whisper.utils import download_model


def srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a media file to SRT locally.")
    parser.add_argument("--file", required=True, help="Input video or audio file.")
    parser.add_argument("--output", required=True, help="Output SRT path.")
    parser.add_argument("--model", default="small", help="faster-whisper model size or path.")
    parser.add_argument("--language", default="zh", help="Language code, for example zh or en.")
    parser.add_argument("--cache-dir", default=".whisper-models", help="Local model cache directory.")
    args = parser.parse_args()

    source = Path(args.file)
    output = Path(args.output)
    cache_dir = Path(args.cache_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    model_dir = cache_dir / args.model
    model_path = download_model(args.model, output_dir=str(model_dir))

    model = WhisperModel(
        model_path,
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        str(source),
        language=args.language,
        beam_size=5,
        vad_filter=True,
    )

    lines = []
    count = 0
    for count, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        lines.append(
            f"{count}\n{srt_time(segment.start)} --> {srt_time(segment.end)}\n{text}\n"
        )

    output.write_text("\n".join(lines), encoding="utf-8-sig")
    print(f"Detected language: {info.language} ({info.language_probability:.2f})")
    print(f"Subtitle segments: {count}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
