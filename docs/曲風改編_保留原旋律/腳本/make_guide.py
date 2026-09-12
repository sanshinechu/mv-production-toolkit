"""把 MIDI 合成成「導引音軌」guide.wav，拿去餵 Suno Cover。

    uv run --python 3.10 --with pretty_midi --with soundfile python make_guide.py melody.mid --bpm 123

產出的是程式合成的單音旋律＋節拍 click。重點不是好聽，是：
  1. 音高輪廓在（Suno Cover 靠這個保住原旋律）
  2. 拍子清楚（click 軌讓 Suno 抓得到速度，這步省掉常常會歪）
  3. 不是任何商業錄音 → 沒有母帶指紋可比對

⚠️ 關於 BPM：Basic Pitch 寫進 MIDI 的速度標記固定是 120，但音符的「秒數」是對的，
   所以旋律本身不需要伸縮。--bpm 只影響 click 軌打在哪裡，一定要給對，
   不然 click 會跟旋律打架。原曲 BPM 用 analyze.py 量：
       uv run --with librosa python ../../參考曲分析_至少還有你搖滾現場版/分析腳本/analyze.py 原曲.mp3
   真的要改變速度請用 --stretch。
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")

FS = 44100
# 疊一點泛音比純正弦好辨識，但泛音一定要壓得夠低。
# 泛音太強，音尾衰減時二次泛音會蓋過基音，音高偵測器（包括 Suno）會聽成高八度。
# 2026-09-12 實測：0.40 的二次泛音會讓 Basic Pitch 把每個音的尾巴抓成高八度的幽靈音。
HARMONICS = [(1, 1.0), (2, 0.14), (3, 0.06)]
DECAY = 1.8                                           # 基音衰減速率


def synth_note(freq, dur, velocity):
    n = max(int(dur * FS), 1)
    t = np.arange(n) / FS
    sig = np.zeros(n)
    for mult, amp in HARMONICS:
        f = freq * mult
        if f < FS / 2:
            # 泛音衰減得比基音快（真實樂器就是這樣），音尾只剩乾淨的基音
            sig += amp * np.sin(2 * np.pi * f * t) * np.exp(-t * DECAY * (1 + 0.8 * (mult - 1)))
    atk = min(int(0.006 * FS), n)                     # 6ms 起音，避免爆音
    sig[:atk] *= np.linspace(0, 1, atk)
    sig *= np.exp(-t * DECAY)
    rel = min(int(0.02 * FS), n)                      # 20ms 收尾
    sig[-rel:] *= np.linspace(1, 0, rel)
    return sig * (velocity / 127.0)


def click_track(total_sec, bpm, offset, level):
    out = np.zeros(int(total_sec * FS) + FS)
    spb = 60.0 / bpm
    n = max(int(0.028 * FS), 1)
    t = np.arange(n) / FS
    env = np.exp(-t * 90)
    beat = 0
    pos = offset
    while pos < total_sec:
        f = 1600 if beat % 4 == 0 else 1000          # 每 4 拍重音
        amp = level * (1.0 if beat % 4 == 0 else 0.6)
        i = int(pos * FS)
        out[i:i + n] += amp * np.sin(2 * np.pi * f * t) * env
        beat += 1
        pos = offset + beat * spb
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("midi", help="melody.mid，或網路下載的現成 MIDI")
    ap.add_argument("--bpm", type=float, default=None,
                    help="原曲 BPM，決定 click 打在哪。不給就用 MIDI 自己的速度標記")
    ap.add_argument("--out", default=None, help="輸出 wav，預設放在 MIDI 旁邊")
    ap.add_argument("--stretch", type=float, default=1.0,
                    help="時間伸縮倍率，>1 變慢。預設 1.0 不動")
    ap.add_argument("--no-click", action="store_true", help="不要節拍軌")
    ap.add_argument("--click-level", type=float, default=0.22)
    ap.add_argument("--click-offset", type=float, default=None,
                    help="第一下 click 的秒數，預設對齊第一個音符")
    ap.add_argument("--max-sec", type=float, default=None,
                    help="只取前 N 秒（Suno 上傳有長度上限，太長就截）")
    ap.add_argument("--transpose", type=int, default=0, help="移調幾個半音")
    args = ap.parse_args()

    src = Path(args.midi).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"找不到檔案：{src}")

    midi = pretty_midi.PrettyMIDI(str(src))
    notes = [n for inst in midi.instruments if not inst.is_drum for n in inst.notes]
    if not notes:
        raise SystemExit("這個 MIDI 裡沒有非鼓的音符。")

    bpm = args.bpm
    if bpm is None:
        tempi, vals = midi.get_tempo_changes()
        bpm = float(vals[0]) if len(vals) else 120.0
        print(f"⚠️  沒給 --bpm，用 MIDI 自己的標記 {bpm:.1f}。"
              f"如果這是 Basic Pitch 的輸出，這個數字幾乎一定是錯的（它固定寫 120）。")

    total = max(n.end for n in notes) * args.stretch
    if args.max_sec:
        total = min(total, args.max_sec)
    audio = np.zeros(int(total * FS) + FS)

    used = 0
    for n in notes:
        start = n.start * args.stretch
        if start >= total:
            continue
        dur = min((n.end - n.start) * args.stretch, total - start)
        freq = pretty_midi.note_number_to_hz(n.pitch + args.transpose)
        sig = synth_note(freq, dur + 0.25, n.velocity)   # 多給 0.25 秒讓尾音自然衰減
        i = int(start * FS)
        audio[i:i + len(sig)] += sig
        used += 1

    if not args.no_click:
        offset = args.click_offset
        if offset is None:
            offset = min(n.start for n in notes) * args.stretch
            offset = offset % (60.0 / bpm)               # 往前對到最近的拍點
        click = click_track(total, bpm, offset, args.click_level)
        audio[:len(click)] += click[:len(audio)]

    peak = np.abs(audio).max()
    if peak > 0:
        audio *= 10 ** (-3 / 20) / peak                  # 峰值壓到 -3 dBFS

    dst = Path(args.out).expanduser().resolve() if args.out else src.with_name(f"{src.stem}_guide.wav")
    sf.write(str(dst), audio.astype(np.float32), FS)

    dur_s = len(audio) / FS
    print(f"\n完成：{dst}")
    print(f"  {used} 個音符，{dur_s // 60:.0f} 分 {dur_s % 60:.0f} 秒，click {bpm:.1f} BPM"
          + ("（無）" if args.no_click else ""))
    print("\n下一步：上傳 Suno → 該首的 ⋯ 選單 → Cover → 填新的 Style 描述。")
    print("  歌詞欄請填 [Instrumental] 或自己寫的新詞，不要貼原詞（會被擋）。")
    print("  Suno 上傳有長度上限，太長就加 --max-sec 截一段最有代表性的。")


if __name__ == "__main__":
    main()
