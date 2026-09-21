#!/usr/bin/env python3
"""Render a non-identity humming guide from the timing and pitch of a vocal stem.

The result deliberately contains no words and does not model the singer's voice.
It follows only voiced timing and F0 so it can be used as a rhythm/pitch guide.
"""

from __future__ import annotations

import argparse
import math

import librosa
import numpy as np
import soundfile as sf


def bridge_short_gaps(mask: np.ndarray, max_gap: int) -> np.ndarray:
    """Keep phrase breaks but bridge tiny unvoiced gaps inside sustained notes."""
    result = mask.copy()
    false_indices = np.flatnonzero(~mask)
    if not len(false_indices):
        return result
    runs = np.split(false_indices, np.where(np.diff(false_indices) != 1)[0] + 1)
    for run in runs:
        start, end = int(run[0]), int(run[-1])
        if len(run) <= max_gap and start > 0 and end < len(mask) - 1 and mask[start - 1] and mask[end + 1]:
            result[start : end + 1] = True
    return result


def f0_to_hum(vocals: np.ndarray, sr: int, hop: int) -> np.ndarray:
    f0, voiced, probability = librosa.pyin(
        vocals,
        fmin=librosa.note_to_hz("A2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=2048,
        hop_length=hop,
        fill_na=np.nan,
    )
    f0 = np.asarray(f0, dtype=float)
    probability = np.nan_to_num(np.asarray(probability, dtype=float))
    valid = np.isfinite(f0) & np.asarray(voiced, dtype=bool) & (probability >= 0.12)
    active = bridge_short_gaps(valid, max_gap=6)  # approximately 70 ms at 22.05 kHz

    # Estimate a stable pitch for brief gaps from nearby voiced frames.
    log_f0 = np.full_like(f0, np.nan)
    log_f0[valid] = np.log(f0[valid])
    active_indices = np.flatnonzero(active)
    if len(active_indices):
        runs = np.split(active_indices, np.where(np.diff(active_indices) != 1)[0] + 1)
        for run in runs:
            known = run[np.isfinite(log_f0[run])]
            if not len(known):
                active[run] = False
                continue
            log_f0[run] = np.interp(run, known, log_f0[known])

    frame_times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop)
    sample_times = np.arange(len(vocals)) / sr
    frequency = np.zeros(len(vocals), dtype=np.float64)
    gate = np.zeros(len(vocals), dtype=np.float64)
    for run in np.split(np.flatnonzero(active), np.where(np.diff(np.flatnonzero(active)) != 1)[0] + 1):
        if not len(run):
            continue
        start_time = frame_times[run[0]]
        end_time = min(len(vocals) / sr, frame_times[run[-1]] + hop / sr)
        samples = np.flatnonzero((sample_times >= start_time) & (sample_times < end_time))
        if not len(samples):
            continue
        frequency[samples] = np.exp(np.interp(sample_times[samples], frame_times[run], log_f0[run]))
        gate[samples] = 1.0

    rms = librosa.feature.rms(y=vocals, frame_length=2048, hop_length=hop, center=True)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    amplitude = np.interp(sample_times, rms_times, rms, left=0.0, right=0.0)
    amplitude = np.clip(amplitude / (np.percentile(amplitude[amplitude > 0], 92) + 1e-9), 0, 1)

    # A gentle fade prevents clicks at consonants and phrase boundaries.
    fade = max(1, round(sr * 0.014))
    gate = np.convolve(gate, np.ones(fade) / fade, mode="same")
    gate = np.convolve(gate, np.ones(fade) / fade, mode="same")
    phase = np.cumsum(2 * math.pi * frequency / sr)
    hum = np.sin(phase) + 0.32 * np.sin(2 * phase) + 0.10 * np.sin(3 * phase) + 0.025 * np.sin(4 * phase)
    hum *= amplitude * gate
    # Smooth the harmonic source slightly so the guide reads as an unworded hum.
    hum = np.convolve(hum, np.ones(5) / 5, mode="same")
    peak = np.max(np.abs(hum))
    return (hum / peak * 0.88 if peak else hum).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("vocals_wav")
    parser.add_argument("output_wav")
    args = parser.parse_args()
    vocals, sr = librosa.load(args.vocals_wav, sr=22050, mono=True)
    hum = f0_to_hum(vocals, sr, hop=256)
    sf.write(args.output_wav, hum, sr, subtype="PCM_16")
    print(f"Rendered {args.output_wav}: {len(hum) / sr:.3f} sec, {sr} Hz")


if __name__ == "__main__":
    main()
