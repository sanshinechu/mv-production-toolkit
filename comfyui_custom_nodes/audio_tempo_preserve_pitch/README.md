# Audio Tempo (Preserve Pitch)

ComfyUI custom node that changes audio tempo with FFmpeg while preserving pitch.

Inputs:

- `audio`: ComfyUI AUDIO input.
- `source_bpm`: measured BPM of the input song.
- `target_bpm`: desired BPM.

Outputs:

- `audio`: time-stretched audio at the original sample rate.
- `duration_seconds`: updated duration for downstream music-generation nodes.

The speed ratio is `target_bpm / source_bpm`. The node automatically builds a
safe FFmpeg `atempo` filter chain when the ratio falls outside `0.5..2.0`.

