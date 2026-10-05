import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
import torch


def _atempo_filter(speed_ratio: float) -> str:
    """Build a quality-preserving FFmpeg atempo chain with factors in 0.5..2.0."""
    factors = []
    remaining = speed_ratio

    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5

    factors.append(remaining)
    return ",".join(f"atempo={factor:.10f}" for factor in factors)


def _write_pcm16_wav(path: Path, waveform: torch.Tensor, sample_rate: int) -> None:
    channels_first = waveform.detach().to(device="cpu", dtype=torch.float32)
    channels_first = channels_first.clamp(-1.0, 1.0)
    pcm = (
        channels_first.transpose(0, 1).contiguous().numpy() * 32767.0
    ).round().astype("<i2")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(pcm.shape[1])
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


def _read_pcm16_wav(path: Path) -> tuple[torch.Tensor, int]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        frames = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2:
        raise RuntimeError(f"Expected 16-bit PCM output, got {sample_width * 8}-bit audio.")

    pcm = np.frombuffer(frames, dtype="<i2").reshape(-1, channels)
    waveform = torch.from_numpy(pcm.copy()).to(dtype=torch.float32) / 32768.0
    return waveform.transpose(0, 1).contiguous(), sample_rate


class AudioTempoPreservePitch:
    """Change music tempo with FFmpeg atempo while preserving pitch."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "source_bpm": (
                    "FLOAT",
                    {"default": 124.0, "min": 20.0, "max": 300.0, "step": 0.1},
                ),
                "target_bpm": (
                    "FLOAT",
                    {"default": 150.0, "min": 20.0, "max": 300.0, "step": 0.1},
                ),
            }
        }

    RETURN_TYPES = ("AUDIO", "FLOAT", "INT")
    RETURN_NAMES = ("audio", "duration_seconds", "target_bpm")
    FUNCTION = "change_tempo"
    CATEGORY = "audio/processing"
    DESCRIPTION = (
        "Changes tempo according to target_bpm / source_bpm while preserving pitch. "
        "Requires FFmpeg in PATH."
    )

    def change_tempo(self, audio, source_bpm, target_bpm):
        if source_bpm <= 0 or target_bpm <= 0:
            raise ValueError("source_bpm and target_bpm must both be greater than zero.")

        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])
        if waveform.ndim != 3:
            raise ValueError(
                f"Expected AUDIO waveform shape [batch, channels, samples], got {tuple(waveform.shape)}."
            )

        speed_ratio = float(target_bpm) / float(source_bpm)
        if abs(speed_ratio - 1.0) < 1e-6:
            duration = float(waveform.shape[-1]) / sample_rate
            return (audio, duration, int(round(target_bpm)))

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg was not found in PATH.")

        processed_batches = []
        with tempfile.TemporaryDirectory(prefix="comfy-audio-tempo-") as temp_dir:
            temp_root = Path(temp_dir)
            for batch_index in range(waveform.shape[0]):
                input_path = temp_root / f"input-{batch_index}.wav"
                output_path = temp_root / f"output-{batch_index}.wav"
                _write_pcm16_wav(input_path, waveform[batch_index], sample_rate)

                command = [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(input_path),
                    "-filter:a",
                    _atempo_filter(speed_ratio),
                    "-ar",
                    str(sample_rate),
                    "-c:a",
                    "pcm_s16le",
                    str(output_path),
                ]
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags,
                    check=False,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        "FFmpeg tempo conversion failed: " + result.stderr.strip()
                    )

                converted, converted_rate = _read_pcm16_wav(output_path)
                if converted_rate != sample_rate:
                    raise RuntimeError(
                        f"Unexpected sample rate {converted_rate}; expected {sample_rate}."
                    )
                processed_batches.append(converted)

        min_samples = min(item.shape[-1] for item in processed_batches)
        processed = torch.stack(
            [item[..., :min_samples] for item in processed_batches], dim=0
        )
        duration = float(processed.shape[-1]) / sample_rate
        return (
            {"waveform": processed, "sample_rate": sample_rate},
            duration,
            int(round(target_bpm)),
        )


NODE_CLASS_MAPPINGS = {
    "AudioTempoPreservePitch": AudioTempoPreservePitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioTempoPreservePitch": "Audio Tempo (Preserve Pitch)",
}
