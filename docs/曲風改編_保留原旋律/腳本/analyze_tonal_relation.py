"""Estimate semitone transposition between two arrangements by chroma correlation."""

from __future__ import annotations

import argparse
import numpy as np
import librosa


def chroma(path: str, start: float, end: float) -> np.ndarray:
    y, sr = librosa.load(path, sr=11025, mono=True, offset=start, duration=end - start)
    c = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=4096, n_fft=4096)
    strength = np.maximum(librosa.feature.rms(y=y, hop_length=4096)[0], 0.001)
    strength = strength[: c.shape[1]]
    c = c[:, : len(strength)]
    v = np.average(c, axis=1, weights=strength)
    return v / np.linalg.norm(v)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("reference")
    p.add_argument("adapted")
    args = p.parse_args()
    windows = [
        ("verse", 34, 92, 18, 53),
        ("chorus", 93, 123, 53, 82),
        ("bridge", 212, 241, 115, 138),
        ("final", 241, 279, 138, 170),
    ]
    for name, rs, re, ts, te in windows:
        a = chroma(args.reference, rs, re)
        b = chroma(args.adapted, ts, te)
        ranked = sorted(
            ((shift, float(a @ np.roll(b, -shift))) for shift in range(12)),
            key=lambda item: item[1],
            reverse=True,
        )
        print(name, ranked[:4])


if __name__ == "__main__":
    main()
