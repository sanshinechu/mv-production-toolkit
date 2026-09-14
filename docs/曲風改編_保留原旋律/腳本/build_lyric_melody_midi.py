"""Build a lyric-ready monophonic MIDI from a rough mapped melody contour."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pretty_midi


# 歌詞受著作權保護，不放在原始碼裡（本 repo 是公開的）。
# 分段歌詞改放本機資料檔，該目錄已列入 .gitignore，說明見 ../README.md。
DEFAULT_LYRICS = Path(__file__).resolve().parent.parent / "歌詞" / "至少還有你_分段歌詞.json"


def load_sections(path: Path) -> list[tuple[float, float, list[str]]]:
    """Read the (start, end, lines) section table from a local JSON file."""
    if not path.exists():
        raise SystemExit(
            f"找不到歌詞資料檔：{path}\n"
            "這個檔含受著作權保護的歌詞，刻意不入版控，所以剛 clone 下來不會有。\n"
            "格式與欄位說明見 ../README.md 的「歌詞資料檔」一節。"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        (float(section["start"]), float(section["end"]), list(section["lines"]))
        for section in data["sections"]
    ]


def clean(text: str) -> str:
    return "".join(re.findall(r"[㐀-鿿]", text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("contour_midi")
    parser.add_argument("output_midi")
    parser.add_argument("output_lyrics")
    parser.add_argument(
        "--lyrics",
        default=str(DEFAULT_LYRICS),
        help="分段歌詞 JSON（預設：../歌詞/至少還有你_分段歌詞.json）",
    )
    args = parser.parse_args()

    sections = load_sections(Path(args.lyrics))

    contour = pretty_midi.PrettyMIDI(args.contour_midi)
    source_notes = [n for inst in contour.instruments for n in inst.notes]

    def pitch_at(time_s: float) -> int:
        active = [n for n in source_notes if n.start <= time_s <= n.end]
        if active:
            return min(active, key=lambda n: abs((n.start + n.end) / 2 - time_s)).pitch
        return min(source_notes, key=lambda n: abs((n.start + n.end) / 2 - time_s)).pitch

    notes: list[pretty_midi.Note] = []
    lyrics: list[str] = []
    for section_start, section_end, raw_lines in sections:
        lines = [clean(line) for line in raw_lines]
        total_chars = sum(len(line) for line in lines)
        cursor = section_start
        usable = section_end - section_start
        for line in lines:
            # Allocate line time by character count, with a short phrase gap.
            line_span = usable * len(line) / total_chars
            phrase_span = line_span * 0.90
            step = phrase_span / len(line)
            for index, lyric in enumerate(line):
                start = cursor + index * step
                end = cursor + (index + 1) * step * 0.96
                notes.append(pretty_midi.Note(
                    velocity=100,
                    pitch=pitch_at((start + end) / 2),
                    start=start,
                    end=end,
                ))
                lyrics.append(lyric)
            cursor += line_span

    midi = pretty_midi.PrettyMIDI(initial_tempo=125.0)
    instrument = pretty_midi.Instrument(program=53, name="Lyric-ready vocal melody")
    instrument.notes = notes
    midi.instruments.append(instrument)
    midi.write(args.output_midi)
    Path(args.output_lyrics).write_text(" ".join(lyrics), encoding="utf-8-sig")
    print(f"notes={len(notes)} lyrics={len(lyrics)} duration={midi.get_end_time():.2f}s")


if __name__ == "__main__":
    main()
