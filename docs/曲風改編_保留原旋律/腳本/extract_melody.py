"""從原曲抽出主旋律，存成 MIDI（路線 B：找不到現成 MIDI 時用）。

    uv run --python 3.10 --with demucs --with basic-pitch python extract_melody.py 原曲.mp3

兩步：Demucs 把人聲跟伴奏拆開 → Basic Pitch 把人聲軌轉成音符。
輸出 melody.mid，接著餵給 make_guide.py 合成導引音軌。

⚠️ Python 要釘 3.10。Basic Pitch 官方支援到 3.10，這台預設的 3.14 裝不起來。
⚠️ 第一次跑會下載 Demucs 模型和 torch（好幾 GB），要等。之後有快取就快了。
⚠️ 抽出來的是「差不多」的旋律，不是樂譜。導引音軌只需要音高輪廓，夠用就好。
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def run_demucs(src: Path, workdir: Path) -> Path:
    """把人聲拆出來。回傳 vocals.wav 的路徑。"""
    print(f"[1/2] Demucs 分離人聲：{src.name}")
    cmd = [sys.executable, "-m", "demucs.separate",
           "--two-stems", "vocals", "-n", "htdemucs",
           "-o", str(workdir), str(src)]
    subprocess.run(cmd, check=True)
    vocals = workdir / "htdemucs" / src.stem / "vocals.wav"
    if not vocals.exists():
        # Demucs 會把檔名裡的某些字元換掉，找不到就掃一下
        found = list((workdir / "htdemucs").glob("*/vocals.wav"))
        if not found:
            raise SystemExit(f"找不到分離結果，預期在 {vocals}")
        vocals = found[0]
    print(f"      → {vocals}")
    return vocals


def drop_octave_ghosts(notes, ratio=0.7):
    """去掉「幽靈八度」。

    音高偵測器常把泛音誤判成獨立的音：跟真正的音同時響、剛好高 12／19／24 個半音、
    而且明顯比較小聲。人聲和合成音都會有這個現象，不濾掉的話旋律會多出一堆假音。
    """
    out = []
    for n in sorted(notes, key=lambda x: (x.start, -x.velocity)):
        active = [m for m in out if m.end > n.start]
        if any((n.pitch - m.pitch) in (12, 19, 24)
               and n.velocity < m.velocity * ratio
               for m in active if m.start < n.end):
            continue
        out.append(n)
    return out


def monophonic(notes, min_len):
    """同一時間只留一個音。導引音軌是單音旋律，和弦會讓 Suno 抓錯重點。

    誰留下來看的是「音量」不是「音高」。偵測器抓出來的假音多半是高八度的泛音，
    用「留最高的」會剛好把真的丟掉、假的留下——2026-09-12 實測踩過這個坑。
    """
    out = []
    for n in sorted(notes, key=lambda x: (x.start, -x.velocity)):
        while out and n.start < out[-1].end and n.velocity > out[-1].velocity:
            # 來了個更響的音，把前一個截短；截到太短就整個丟掉，再往前檢查一次
            out[-1].end = n.start
            if out[-1].end - out[-1].start >= min_len:
                break
            out.pop()
        if out and n.start < out[-1].end:
            # 前一個音比較響，這個音讓位
            if n.end - out[-1].end >= min_len:
                n.start = out[-1].end
                out.append(n)
            continue
        out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="原曲音檔（mp3/wav/flac…）")
    ap.add_argument("--outdir", default=None,
                    help="輸出位置，預設放在原曲旁邊")
    ap.add_argument("--skip-demucs", action="store_true",
                    help="輸入已經是乾淨的人聲軌或單音演奏，不用再分離")
    ap.add_argument("--keep-polyphonic", action="store_true",
                    help="保留和弦，不壓成單音線")
    ap.add_argument("--keep-ghosts", action="store_true",
                    help="不要濾掉高八度的泛音假音（真的有高八度和聲時才用）")
    ap.add_argument("--min-note-ms", type=float, default=100,
                    help="比這短的音視為雜訊丟掉（預設 100ms）")
    args = ap.parse_args()

    src = Path(args.audio).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"找不到檔案：{src}")
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)

    vocals = src if args.skip_demucs else run_demucs(src, outdir / "_stems")

    print(f"[2/2] Basic Pitch 抽音符：{vocals.name}")
    from basic_pitch.inference import predict

    _, midi, _ = predict(str(vocals), minimum_note_length=args.min_note_ms)

    min_len = args.min_note_ms / 1000.0
    for inst in midi.instruments:
        inst.pitch_bends = []          # Basic Pitch 塞的彎音，合成出來會走音
        inst.control_changes = []
        inst.program = 0               # Acoustic Grand Piano
        inst.notes = [n for n in inst.notes if n.end - n.start >= min_len]
        if not args.keep_ghosts:
            inst.notes = drop_octave_ghosts(inst.notes)
        if not args.keep_polyphonic:
            inst.notes = monophonic(inst.notes, min_len)

    notes = [n for i in midi.instruments for n in i.notes]
    if not notes:
        raise SystemExit("一個音都沒抽到。試試 --min-note-ms 調小，或換一首人聲清楚一點的。")

    dst = outdir / f"{src.stem}_melody.mid"
    midi.write(str(dst))

    import pretty_midi
    lo, hi = min(n.pitch for n in notes), max(n.pitch for n in notes)
    print(f"\n完成：{dst}")
    print(f"  音符 {len(notes)} 個，長度 {max(n.end for n in notes):.1f} 秒")
    print(f"  音域 {pretty_midi.note_number_to_name(lo)} ~ {pretty_midi.note_number_to_name(hi)}")
    print(f"\n下一步：先用 analyze.py 量原曲 BPM，再跑")
    print(f"  uv run --python 3.10 --with pretty_midi --with soundfile \\")
    print(f"      python make_guide.py \"{dst}\" --bpm <原曲BPM>")


if __name__ == "__main__":
    main()
