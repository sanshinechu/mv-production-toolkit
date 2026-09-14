"""Map selected reference-song MIDI windows onto an adapted song timeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pretty_midi


# source start/end -> adapted start/end, all in seconds.
SEGMENTS = [
    (34.0, 92.0, 18.0, 53.0),   # verse + pre-chorus
    (96.0, 128.0, 53.0, 82.0),  # first chorus
    (211.0, 246.0, 115.0, 138.0),  # bridge
    (249.0, 282.0, 138.0, 170.0),  # final chorus
    (282.0, 298.0, 170.0, 186.0),  # outro
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()

    source = pretty_midi.PrettyMIDI(args.source)
    source_notes = [note for inst in source.instruments for note in inst.notes]
    mapped: list[pretty_midi.Note] = []
    for src_start, src_end, dst_start, dst_end in SEGMENTS:
        scale = (dst_end - dst_start) / (src_end - src_start)
        for note in source_notes:
            if note.start < src_start or note.start >= src_end:
                continue
            start = dst_start + (note.start - src_start) * scale
            end = dst_start + (min(note.end, src_end) - src_start) * scale
            if end - start < 0.07:
                end = start + 0.07
            mapped.append(pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=start,
                end=min(end, dst_end),
            ))

    mapped.sort(key=lambda n: n.start)
    for left, right in zip(mapped, mapped[1:]):
        if left.end > right.start:
            left.end = max(left.start + 0.04, right.start)

    output = pretty_midi.PrettyMIDI(initial_tempo=125.0)
    lead = pretty_midi.Instrument(program=53, name="Adapted vocal melody draft")
    lead.notes = mapped
    output.instruments.append(lead)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.write(str(out_path))
    print(f"mapped_notes={len(mapped)} duration={output.get_end_time():.2f}s output={out_path}")


if __name__ == "__main__":
    main()
