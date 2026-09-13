"""Snap an OpenUtau USTX vocal onto the real beat grid of its backing track.

Why this exists (measured on 至少還有你, 2026-09-13):
- Suno backings drift in tempo (123.8 -> 126 -> 122.3 BPM across one song), so a
  single project BPM puts OpenUtau's grid lines up to 150 ms away from the drums.
- Folding each note into the singer's range on its own creates 12-semitone jumps
  inside a phrase, which sounds like singing out of tune.

What it does (the source USTX is only read; the output must be a new path):
1. tracks every beat of the backing and writes a per-beat tempo map, so the
   OpenUtau grid lines sit exactly on the backing's beats
2. snaps note onsets to the nearest 1/8 beat, or 1/16 when the 1/8 is too far
3. undoes octave folds inside a phrase, then moves the whole phrase by octaves
   to fit the singer's range, so melodic intervals survive
4. reports notes whose pitch class is weak in the backing harmony

The audio timing of notes changes only by the snap; the tempo map just makes the
editor's grid match the backing so later hand edits land on the beat.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import yaml
from scipy.signal import savgol_filter

PC_NAMES = "C C# D D# E F F# G G# A A# B".split()
SR = 22050
HOP = 256


def tempo_map(project: dict) -> tuple[int, list[dict]]:
    tempos = project.get("tempos") or [{"position": 0, "bpm": project["bpm"]}]
    return project["resolution"], sorted(tempos, key=lambda t: t["position"])


def ticks_to_seconds(tick: float, resolution: int, tempos: list[dict]) -> float:
    seconds = 0.0
    for i, tempo in enumerate(tempos):
        start = tempo["position"]
        end = tempos[i + 1]["position"] if i + 1 < len(tempos) else float("inf")
        if tick <= start:
            break
        seconds += (min(tick, end) - start) / resolution * 60.0 / tempo["bpm"]
    return seconds


def track_beats(y: np.ndarray, duration: float) -> tuple[np.ndarray, int, float]:
    _, frames = librosa.beat.beat_track(y=y, sr=SR, hop_length=HOP, tightness=400)
    raw = librosa.frames_to_time(frames, sr=SR, hop_length=HOP)
    ibi = np.diff(raw)
    odd = int((np.abs(ibi / np.median(ibi) - 1) > 0.3).sum())
    # Tracked beats jitter by a frame or a misplaced onset (single intervals read
    # 107-132 BPM while the 16-beat average only drifts 122-126). Smooth the
    # beat-time curve so the grid follows the tempo drift but not the jitter.
    beats = savgol_filter(raw, window_length=min(17, len(raw) // 2 * 2 - 1), polyorder=2)
    jitter_ms = float(np.max(np.abs(beats - raw)) * 1000)
    ibi = np.diff(beats)
    head, tail = np.median(ibi[:8]), np.median(ibi[-8:])
    # Keep the first beat between one and two beat lengths from 0 s, so the
    # lead-in tempo entry stays in a sane BPM range.
    while beats[0] > 2 * head:
        beats = np.insert(beats, 0, beats[0] - head)
    if beats[0] < head:
        beats = beats[1:]
    while beats[-1] < duration + tail:
        beats = np.append(beats, beats[-1] + tail)
    return beats, odd, jitter_ms


def downbeat_phase(y: np.ndarray, beats: np.ndarray) -> tuple[int, list[float]]:
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
    low = librosa.onset.onset_strength(
        S=librosa.amplitude_to_db(spec[freqs < 150]), sr=SR, hop_length=HOP)
    frames = np.minimum(librosa.time_to_frames(beats, sr=SR, hop_length=HOP), len(low) - 1)
    scores = [float(np.mean(low[frames[p::4]])) for p in range(4)]
    return int(np.argmax(scores)), scores


def fix_octaves(tones, starts, ends, lo, hi, leap, phrase_gap, overshoot):
    tones = list(tones)
    out = list(tones)
    kind = [""] * len(tones)
    bounds = [0] + [i + 1 for i in range(len(tones) - 1)
                    if starts[i + 1] - ends[i] >= phrase_gap] + [len(tones)]
    for a, b in zip(bounds, bounds[1:]):
        unwrapped = [tones[a]]
        for x in tones[a + 1:b]:
            while x - unwrapped[-1] >= leap:
                x -= 12
            while unwrapped[-1] - x >= leap:
                x += 12
            unwrapped.append(x)
        median = float(np.median(tones[a:b]))

        def cost(shift):
            moved = [v + shift for v in unwrapped]
            outside = sum(max(0, lo - v) + max(0, v - hi) for v in moved)
            return outside, abs(float(np.median(moved)) - median)

        shift = min((-24, -12, 0, 12, 24), key=cost)
        for i, v in zip(range(a, b), unwrapped):
            v += shift
            if v > hi + overshoot:
                v -= 12
                kind[i] = "range-fold"
            elif v < lo - overshoot:
                v += 12
                kind[i] = "range-fold"
            elif v != tones[i]:
                kind[i] = "octave-fix"
            out[i] = v
    return out, kind


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source_ustx")
    p.add_argument("backing_audio")
    p.add_argument("output_ustx")
    p.add_argument("--report", help="CSV with per-note changes and harmony check")
    p.add_argument("--preview", help="WAV: backing plus a plain synth of the snapped melody")
    p.add_argument("--tol-ms", type=float, default=45.0, help="max move to reach a 1/8 beat before trying 1/16")
    p.add_argument("--range", nargs=2, type=int, default=(55, 70), metavar=("LOW", "HIGH"))
    p.add_argument("--overshoot", type=int, default=2, help="semitones allowed past the range before folding")
    p.add_argument("--leap", type=int, default=10, help="in-phrase jump size treated as an octave fold")
    p.add_argument("--phrase-gap", type=float, default=0.15, help="silence (s) that starts a new phrase")
    p.add_argument("--downbeat-phase", default="auto", help="auto, or 0-3: which tracked beat is beat 1")
    p.add_argument("--no-octave-fix", action="store_true")
    args = p.parse_args()

    source_path = Path(args.source_ustx).resolve()
    output_path = Path(args.output_ustx).resolve()
    if source_path == output_path:
        raise ValueError("Output must be a new project path, not the original")

    project = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    resolution, tempos = tempo_map(project)
    part = project["voice_parts"][0]
    notes = sorted(part["notes"], key=lambda n: n["position"])
    base = part.get("position", 0)
    starts = np.array([ticks_to_seconds(base + n["position"], resolution, tempos) for n in notes])
    ends = np.array([ticks_to_seconds(base + n["position"] + n["duration"], resolution, tempos) for n in notes])

    y, _ = librosa.load(args.backing_audio, sr=SR, mono=True)
    duration = len(y) / SR
    beats, odd, jitter_ms = track_beats(y, duration)
    local_bpm = 60.0 / np.diff(beats)
    print(f"beats={len(beats)} odd_intervals={odd} max_smoothing_move={jitter_ms:.0f}ms bpm min/median/max="
          f"{local_bpm.min():.1f}/{np.median(local_bpm):.1f}/{local_bpm.max():.1f}")

    if args.downbeat_phase == "auto":
        phase, scores = downbeat_phase(y, beats)
        print(f"downbeat phase auto={phase} (low-band accent {np.round(scores, 2).tolist()}; only affects bar lines)")
    else:
        phase = int(args.downbeat_phase) % 4
    lead = (4 - phase - 1) % 4 + 1  # lead-in beats so tick 0 is a bar line
    beat_index = np.concatenate(([-lead], np.arange(len(beats))))
    beat_times = np.concatenate(([0.0], beats))

    def beat_of(t):
        return np.interp(t, beat_times, beat_index)

    def time_of(b):
        return np.interp(b, beat_index, beat_times)

    tol = args.tol_ms / 1000.0
    new_b, grid = [], []
    for t in starts:
        b = float(beat_of(t))
        eighth = round(b * 2) / 2
        if abs(time_of(eighth) - t) <= tol:
            nb, g = eighth, "1/8"
        else:
            nb, g = round(b * 4) / 4, "1/16"
        if new_b and nb < new_b[-1] + 0.25:
            nb, g = new_b[-1] + 0.25, "1/16 pushed"
        new_b.append(nb)
        grid.append(g)

    end_b = []
    for i, e in enumerate(ends):
        nxt = new_b[i + 1] if i + 1 < len(notes) else None
        if nxt is not None and starts[i + 1] - e <= 0.12:
            eb = nxt
        else:
            eb = max(new_b[i] + 0.25, round(float(beat_of(e)) * 4) / 4)
            if nxt is not None:
                eb = min(eb, nxt)
        end_b.append(eb)

    old_tones = [n["tone"] for n in notes]
    if args.no_octave_fix:
        new_tones, kinds = list(old_tones), [""] * len(notes)
    else:
        new_tones, kinds = fix_octaves(old_tones, starts, ends, *args.range, args.leap,
                                       args.phrase_gap, args.overshoot)

    def tick(b):
        return int(round((b + lead) * resolution))

    for n, sb, eb, tone in zip(notes, new_b, end_b, new_tones):
        n["position"] = tick(sb) - base
        n["duration"] = tick(eb) - tick(sb)
        n["tone"] = int(tone)

    # numpy scalars must become plain Python numbers or yaml.safe_dump refuses them
    new_tempos = [{"position": 0, "bpm": round(float(60.0 * lead / beats[0]), 4)}]
    new_tempos += [{"position": tick(k), "bpm": round(float(60.0 / (beats[k + 1] - beats[k])), 4)}
                   for k in range(len(beats) - 1)]
    project["tempos"] = new_tempos
    project["bpm"] = round(float(np.median(local_bpm)), 3)
    part["notes"] = notes
    part["duration"] = max(part["duration"], tick(float(beat_of(duration))) + resolution - base)
    part["name"] = f"{part['name']}・拍點對齊"

    # Harmony check against the backing's harmonic component.
    chroma = librosa.feature.chroma_cqt(y=librosa.effects.harmonic(y), sr=SR, hop_length=512)
    new_start_s = [float(time_of(b)) for b in new_b]
    new_end_s = [float(time_of(b)) for b in end_b]
    ranks = []
    for s, e, tone in zip(new_start_s, new_end_s, new_tones):
        f0 = librosa.time_to_frames(s, sr=SR, hop_length=512)
        f1 = max(f0 + 1, librosa.time_to_frames(e, sr=SR, hop_length=512))
        v = chroma[:, f0:f1].mean(axis=1)
        ranks.append(int(1 + (v > v[tone % 12]).sum()))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(project, allow_unicode=True, sort_keys=False, width=120),
                           encoding="utf-8")

    shifts = (np.array(new_start_s) - starts) * 1000
    # rank>4 flagged 104 of 301 notes on 至少還有你 — mostly chroma noise from
    # distorted guitars. rank>=9 (bottom third of 12 pitch classes) keeps ~46
    # and they cluster where the backing really reharmonised (the bridge).
    weak = [i for i, r in enumerate(ranks) if r >= 9 and new_end_s[i] - new_start_s[i] >= 0.35]
    print(f"notes={len(notes)} onset move ms p50/p90/max="
          f"{np.percentile(abs(shifts), 50):.0f}/{np.percentile(abs(shifts), 90):.0f}/{abs(shifts).max():.0f}")
    print(f"grid: 1/8={grid.count('1/8')} 1/16={grid.count('1/16')} pushed={grid.count('1/16 pushed')}")
    print(f"octave-fix={kinds.count('octave-fix')} range-fold={kinds.count('range-fold')} "
          f"tone range {min(new_tones)}-{max(new_tones)}")
    print(f"long notes clashing with backing harmony (rank>=9 of 12): {len(weak)}")
    for i in weak[:15]:
        print(f"  {new_start_s[i]:7.2f}s {notes[i]['lyric']} {PC_NAMES[new_tones[i] % 12]}{new_tones[i] // 12 - 1} rank {ranks[i]}")
    print(output_path)

    if args.report:
        with open(args.report, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["index", "lyric", "old_start_s", "new_start_s", "move_ms", "grid",
                        "old_tone", "new_tone", "octave_change", "harmony_rank", "weak_long_note"])
            for i, n in enumerate(notes):
                w.writerow([i, n["lyric"], f"{starts[i]:.3f}", f"{new_start_s[i]:.3f}", f"{shifts[i]:.0f}",
                            grid[i], old_tones[i], new_tones[i], kinds[i], ranks[i], "Y" if i in weak else ""])
        print(args.report)

    if args.preview:
        out_sr = 44100
        backing, _ = librosa.load(args.backing_audio, sr=out_sr, mono=False)
        backing = np.atleast_2d(backing)
        synth = np.zeros(backing.shape[1])
        for s, e, tone in zip(new_start_s, new_end_s, new_tones):
            i0, i1 = int(s * out_sr), min(int(e * out_sr), len(synth))
            if i1 <= i0:
                continue
            t = np.arange(i1 - i0) / out_sr
            hz = 440.0 * 2 ** ((tone - 69) / 12)
            wave = np.sin(2 * np.pi * hz * t) + 0.3 * np.sin(4 * np.pi * hz * t)
            env = np.minimum(1, np.minimum(t / 0.01, (t[-1] - t) / 0.03 + 1e-9))
            synth[i0:i1] += wave * env
        synth *= 0.35 / max(1e-9, np.abs(synth).max())
        mix = (backing * 0.7 + synth).T
        mix /= max(1.0, np.abs(mix).max() / 0.98)
        sf.write(args.preview, mix, out_sr)
        print(args.preview)


if __name__ == "__main__":
    main()
