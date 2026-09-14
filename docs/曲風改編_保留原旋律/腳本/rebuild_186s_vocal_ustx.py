"""Rebuild the 186 s OpenUtau vocal part from the separated reference singer.

This is an editable alignment draft, not a claim of note-perfect transcription.
The existing .ustx is only read; the output must be a different path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pretty_midi
import yaml


# 歌詞受著作權保護，不放在原始碼裡（本 repo 是公開的）。
# 逐句對位表（改編秒數、參考版秒數、該句歌詞）改放本機資料檔，
# 該目錄已列入 .gitignore，說明見 ../README.md。
DEFAULT_PHRASES = Path(__file__).resolve().parent.parent / "歌詞" / "至少還有你_逐句對位.json"


def load_phrases(path: Path) -> list[tuple[float, float, float, float, str]]:
    """Read the phrase alignment table from a local JSON file.

    Each row is (adapted start, adapted end, reference start, reference end, lyric).
    """
    if not path.exists():
        raise SystemExit(
            f"找不到逐句對位資料檔：{path}\n"
            "這個檔含受著作權保護的歌詞，刻意不入版控，所以剛 clone 下來不會有。\n"
            "格式與欄位說明見 ../README.md 的「歌詞資料檔」一節。"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        (
            float(row["target_start"]),
            float(row["target_end"]),
            float(row["source_start"]),
            float(row["source_end"]),
            row["lyric"],
        )
        for row in data["phrases"]
    ]


def ria_register(pitch: int) -> int:
    """Fold Basic Pitch octave ghosts into Ria's documented low register.

    The bank author states A2-G#4 (45-68). A#4 (70) is retained as a small
    climax overshoot; the bank's pitch augmentation covers a few semitones.
    """
    while pitch < 55:
        pitch += 12
    while pitch > 70:
        pitch -= 12
    return pitch


def note_template(lyric: str, tick: int, duration: int, tone: int) -> dict:
    return {
        "position": tick,
        "duration": duration,
        "tone": tone,
        "lyric": lyric,
        "pitch": {
            "data": [
                {"x": -40, "y": 0, "shape": "io"},
                {"x": 40, "y": 0, "shape": "io"},
            ],
            "snap_first": True,
        },
        "vibrato": {
            "length": 35 if duration >= 650 else 0,
            "period": 175,
            "depth": 18,
            "in": 10,
            "out": 10,
            "shift": 0,
            "drift": 0,
            "vol_link": 0,
        },
        "phoneme_expressions": [],
        "phoneme_overrides": [],
    }


def aligned_phrase(
    source: list[pretty_midi.Note],
    target_start: float,
    target_end: float,
    source_start: float,
    source_end: float,
    lyrics: str,
    ticks_per_second: float,
) -> list[dict]:
    candidates = sorted(
        (n for n in source if source_start <= n.start < source_end),
        key=lambda n: n.start,
    )
    if not candidates:
        raise ValueError(f"No reference vocal notes at {source_start}-{source_end}")

    # Rank-resample the singer's note onsets to the number of sung syllables.
    # This preserves the phrase's long/short rhythm much better than equal spacing.
    count = len(lyrics)
    selected = [
        candidates[min(len(candidates) - 1, int((i + 0.5) * len(candidates) / count))]
        for i in range(count)
    ]
    raw = [max(0.0, min(1.0, (n.start - source_start) / (source_end - source_start))) for n in selected]
    # Sung note detection has spurious short ornaments and sometimes misses a
    # whole syllable. Keep its rhythmic shape, but anchor it to a steady lyric
    # progression so it cannot bunch characters or hold one character for ages.
    fractions = [0.45 * detected + 0.55 * ((i + 0.5) / count)
                 for i, detected in enumerate(raw)]
    # Duplicated selected notes need a distinct attack for each character.
    min_step = min(0.205, 0.75 * (target_end - target_start) / count)
    available = target_end - target_start - 0.2
    starts: list[float] = []
    for i, fraction in enumerate(fractions):
        desired = target_start + 0.08 + fraction * available
        if starts:
            desired = max(desired, starts[-1] + min_step)
        starts.append(desired)
    if starts[-1] > target_end - 0.22:
        factor = (target_end - 0.22 - starts[0]) / (starts[-1] - starts[0])
        starts = [starts[0] + (s - starts[0]) * factor for s in starts]

    result = []
    for i, (lyric, source_note, start) in enumerate(zip(lyrics, selected, starts)):
        following = starts[i + 1] if i + 1 < count else target_end - 0.10
        duration = max(0.18, min(following - start - 0.025, 1.0))
        result.append(note_template(
            lyric,
            round(start * ticks_per_second),
            max(100, round(duration * ticks_per_second)),
            ria_register(source_note.pitch),
        ))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_ustx")
    parser.add_argument("reference_vocal_midi")
    parser.add_argument("output_ustx")
    parser.add_argument(
        "--phrases",
        default=str(DEFAULT_PHRASES),
        help="逐句對位 JSON（預設：../歌詞/至少還有你_逐句對位.json）",
    )
    args = parser.parse_args()
    source_path = Path(args.source_ustx).resolve()
    output_path = Path(args.output_ustx).resolve()
    if source_path == output_path:
        raise ValueError("Output must be a new project path, not the original")
    phrases = load_phrases(Path(args.phrases))
    project = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    midi = pretty_midi.PrettyMIDI(args.reference_vocal_midi)
    vocal_notes = [note for inst in midi.instruments for note in inst.notes]
    tick_rate = project["resolution"] * project["tempos"][0]["bpm"] / 60.0
    new_notes = []
    for t0, t1, s0, s1, lyrics in phrases:
        new_notes.extend(aligned_phrase(vocal_notes, t0, t1, s0, s1, lyrics, tick_rate))
    new_notes.sort(key=lambda note: note["position"])
    for left, right in zip(new_notes, new_notes[1:]):
        if left["position"] + left["duration"] > right["position"]:
            left["duration"] = max(100, right["position"] - left["position"] - 20)
    project["voice_parts"][0]["notes"] = new_notes
    last_tick = max(note["position"] + note["duration"] for note in new_notes)
    project["voice_parts"][0]["duration"] = max(
        project["voice_parts"][0]["duration"],
        round(186.0 * tick_rate),
        last_tick + 100,
    )
    project["voice_parts"][0]["name"] = "Ria 女聲・分離主唱對齊草稿"
    project["tracks"][1]["track_name"] = "Ria 女聲・分離主唱對齊草稿"
    project["tracks"][1]["phonemizer"] = "OpenUtau.Core.DiffSinger.DiffSingerChinesePhonemizer"
    project["tracks"][1]["renderer_settings"]["renderer"] = "DIFFSINGER"
    project["name"] = "至少還有你・186 秒女聲修正版"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(project, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"notes={len(new_notes)} first={new_notes[0]['position']/tick_rate:.2f}s "
          f"last={(new_notes[-1]['position']+new_notes[-1]['duration'])/tick_rate:.2f}s")
    print(f"pitch_range={min(n['tone'] for n in new_notes)}-{max(n['tone'] for n in new_notes)}")
    print(output_path)


if __name__ == "__main__":
    main()
