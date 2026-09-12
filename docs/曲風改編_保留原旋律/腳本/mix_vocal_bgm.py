"""把原唱人聲疊到 Suno 生的新伴奏上。

    uv run --python 3.10 --with librosa --with soundfile python mix_vocal_bgm.py \
        vocals.wav suno_rock.mp3 --out 成品.wav

兩軌都源自同一首原曲的時間軸（guide.wav 走的就是原曲時間），所以理論上對得上。
腳本會自己用起音包絡互相關算最佳位移，速度差太多時會警告並可選擇伸縮。

先跑 --dry-run 看分析結果，確認速度和長度合理再真的輸出。
"""
import argparse
import sys

import numpy as np
import librosa
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")

SR = 44100


HOP = 512


def chroma_of(y, sr):
    """音高輪廓。用它而不是起音包絡來對齊——起音只看「哪裡有鼓點」，
    重複的段落每一拍長得都像，互相關會對到隔壁那一拍去。
    2026-09-12 實測：已知 1.750 秒的位移被起音法算成 1.265 秒，剛好差一整拍。
    chroma 分得出 C 和 G，差一拍就對不上，能破解這種歧義。"""
    c = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP)
    return (c - c.mean(axis=1, keepdims=True)) / (c.std(axis=1, keepdims=True) + 1e-9)


def best_offset(a, b, sr, max_shift_sec=30, topn=3):
    """找 b 相對 a 的最佳位移（秒）。正值＝b 要往後推。回傳前幾名候選。"""
    ca, cb = chroma_of(a, sr), chroma_of(b, sr)
    n = int(max_shift_sec * sr / HOP)
    centre = cb.shape[1] - 1
    total = None
    for k in range(12):                       # 12 個半音各自相關再相加
        c = np.correlate(ca[k], cb[k], mode="full")
        total = c if total is None else total + c
    lo, hi = max(0, centre - n), min(len(total), centre + n + 1)
    seg = total[lo:hi] / (min(ca.shape[1], cb.shape[1]) * 12 + 1e-9)

    # 取彼此相隔夠遠的前幾個峰，避免同一個峰被算成好幾名
    cands, taken = [], np.zeros(len(seg), bool)
    guard = int(0.25 * sr / HOP)
    for _ in range(topn):
        masked = np.where(taken, -np.inf, seg)
        k2 = int(np.argmax(masked))
        if not np.isfinite(masked[k2]):
            break
        cands.append(((k2 + lo - centre) * HOP / sr, float(seg[k2])))
        taken[max(0, k2 - guard):k2 + guard + 1] = True
    return cands


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vocals", help="Demucs 分離出來的人聲軌")
    ap.add_argument("bgm", help="Suno 生的新伴奏")
    ap.add_argument("--out", default="mixed.wav")
    ap.add_argument("--offset", type=float, default=None,
                    help="手動指定伴奏相對人聲的位移（秒），不給就自動偵測")
    ap.add_argument("--stretch", action="store_true",
                    help="把伴奏伸縮到跟人聲一樣長（速度差很多時才用，音質會打折）")
    ap.add_argument("--vocal-gain", type=float, default=0.0, help="人聲增益 dB")
    ap.add_argument("--bgm-gain", type=float, default=-2.0, help="伴奏增益 dB，預設壓一點讓人聲出來")
    ap.add_argument("--dry-run", action="store_true", help="只分析不輸出")
    args = ap.parse_args()

    print("載入中…")
    v, _ = librosa.load(args.vocals, sr=SR, mono=True)
    b, _ = librosa.load(args.bgm, sr=SR, mono=True)

    tv = float(np.atleast_1d(librosa.beat.beat_track(y=v, sr=SR)[0])[0])
    tb = float(np.atleast_1d(librosa.beat.beat_track(y=b, sr=SR)[0])[0])
    print(f"\n人聲：{len(v)/SR:6.1f} 秒   {tv:6.1f} BPM")
    print(f"伴奏：{len(b)/SR:6.1f} 秒   {tb:6.1f} BPM")

    drift = abs(tv - tb) / max(tv, tb)
    if drift > 0.03:
        print(f"⚠️  速度差 {drift*100:.1f}%，疊起來會逐漸走掉。"
              f"建議回 Suno 重生一首速度接近的，或加 --stretch 硬拉。")
    else:
        print(f"   速度差 {drift*100:.1f}%，可以疊。")

    if args.stretch:
        rate = len(b) / len(v)
        print(f"   伸縮伴奏 ×{1/rate:.4f} 對齊人聲長度…")
        b = librosa.effects.time_stretch(b, rate=rate)

    if args.offset is None:
        cands = best_offset(v, b, SR)
        off, score = cands[0]
        print(f"\n自動偵測位移：{off:+.3f} 秒（相關度 {score:.3f}）")
        if len(cands) > 1:
            print("   其他候選：" + "，".join(f"{o:+.3f}s({c:.3f})" for o, c in cands[1:]))
            if cands[1][1] > score * 0.9:
                print("⚠️  第二名分數很接近，對齊可能有歧義。"
                      "先用 --dry-run 搭 --offset 逐個試聽再決定。")
        if score < 0.05:
            print("⚠️  相關度很低，自動對齊可能不準。先 --dry-run 試幾個 --offset 手動找。")
    else:
        off = args.offset
        print(f"\n手動位移：{off:+.3f} 秒")

    if args.dry_run:
        print("\n（--dry-run，沒有輸出檔案）")
        return

    # 混音時載入立體聲（若輸入為單聲道則自動擴充為雙聲道）
    v_stereo, _ = librosa.load(args.vocals, sr=SR, mono=False)
    b_stereo, _ = librosa.load(args.bgm, sr=SR, mono=False)
    if v_stereo.ndim == 1:
        v_stereo = np.stack([v_stereo, v_stereo])
    if b_stereo.ndim == 1:
        b_stereo = np.stack([b_stereo, b_stereo])

    if args.stretch:
        rate = b_stereo.shape[1] / v_stereo.shape[1]
        b_stereo = np.stack([
            librosa.effects.time_stretch(b_stereo[0], rate=rate),
            librosa.effects.time_stretch(b_stereo[1], rate=rate)
        ])

    shift = int(round(off * SR))
    n = max(v_stereo.shape[1], b_stereo.shape[1] + max(shift, 0))
    mix = np.zeros((2, n))
    mix[:, :v_stereo.shape[1]] += v_stereo * 10 ** (args.vocal_gain / 20)
    s = max(shift, 0)
    bb = b_stereo[:, max(-shift, 0):]
    mix[:, s:s + bb.shape[1]] += bb * 10 ** (args.bgm_gain / 20)

    peak = np.abs(mix).max()
    if peak > 0:
        mix *= 10 ** (-1 / 20) / peak          # 峰值壓到 -1 dBFS，避免削波

    sf.write(args.out, mix.T.astype(np.float32), SR)
    print(f"\n完成（立體聲）：{args.out}  ({mix.shape[1]/SR:.1f} 秒)")
    print("聽的時候注意：副歌人聲會不會被伴奏蓋掉（調 --bgm-gain），")
    print("以及後半段有沒有逐漸失去同步（那就是速度差，要 --stretch 或重生）。")


if __name__ == "__main__":
    main()
