"""Extract a conservative monophonic vocal-line draft from a polyphonic MIDI."""

from __future__ import annotations

import argparse
from pathlib import Path

import pretty_midi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--low", type=int, default=55)
    parser.add_argument("--high", type=int, default=81)
    args = parser.parse_args()

    midi = pretty_midi.PrettyMIDI(args.source)
    candidates = [
        note
        for instrument in midi.instruments
        for note in instrument.notes
        if args.low <= note.pitch <= args.high
        and note.end - note.start >= 0.10
        and note.velocity >= 30
    ]
    candidates.sort(key=lambda n: (n.start, -n.pitch, -n.velocity))

    # Collapse near-simultaneous chord tones. The vocal melody is usually the
    # upper sustained tone; continuity wins when an alternative is available.
    groups: list[list[pretty_midi.Note]] = []
    for note in candidates:
        if not groups or note.start - groups[-1][0].start > 0.065:
            groups.append([note])
        else:
            groups[-1].append(note)

    chosen: list[pretty_midi.Note] = []
    previous_pitch: int | None = None
    previous_end = 0.0
    for group in groups:
        def score(note: pretty_midi.Note) -> float:
            duration = min(note.end - note.start, 1.5)
            continuity = 0.0 if previous_pitch is None else -2.2 * abs(note.pitch - previous_pitch)
            upper_voice = 0.65 * note.pitch
            return note.velocity + 16.0 * duration + continuity + upper_voice

        pick = max(group, key=score)
        start = max(pick.start, previous_end)
        end = max(start + 0.10, pick.end)
        if chosen and start - chosen[-1].end < 0.045 and pick.pitch == chosen[-1].pitch:
            chosen[-1].end = max(chosen[-1].end, end)
            previous_end = chosen[-1].end
            continue
        if start < end:
            clean = pretty_midi.Note(
                velocity=max(70, pick.velocity), pitch=pick.pitch, start=start, end=end
            )
            chosen.append(clean)
            previous_pitch = pick.pitch
            previous_end = end

    output = pretty_midi.PrettyMIDI(initial_tempo=125.0)
    lead = pretty_midi.Instrument(program=53, name="Vocal melody draft")
    lead.notes = chosen
    output.instruments.append(lead)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.write(str(out_path))
    print(f"source_notes={len(candidates)} output_notes={len(chosen)} output={out_path}")


if __name__ == "__main__":
    main()
