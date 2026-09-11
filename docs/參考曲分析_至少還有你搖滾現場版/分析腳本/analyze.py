"""歌曲結構分析：速度、調性、每 5 秒能量／鼓／低音比例、自動段落切分。

用法：
    uv run --with librosa python analyze.py 歌曲.mp3

輸出：印在畫面上，另存 persec.json（每秒數據，可拿去畫圖）。
"""
import sys, json
import numpy as np
import librosa

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr
print(f"duration {dur:.1f}s")

# --- 速度：整首與每 30 秒
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
bt = librosa.frames_to_time(beats, sr=sr)
print("global tempo", np.round(tempo, 1))
ibi = np.diff(bt)
for a in range(0, int(dur), 30):
    m = (bt[1:] >= a) & (bt[1:] < a + 30)
    if m.sum() > 2:
        print(f"  tempo {a:3d}-{a+30:3d}s: {60/np.median(ibi[m]):.1f} bpm")

# --- 調性：Krumhansl-Schmuckler，整首與每 15 秒（看有沒有升 Key）
maj = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
mnr = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
names = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]
y_h, y_p = librosa.effects.hpss(y)
chroma = librosa.feature.chroma_cqt(y=y_h, sr=sr, hop_length=512)
ct = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
def key_of(c):
    best = None
    for i in range(12):
        for prof, q in ((maj, "maj"), (mnr, "min")):
            r = np.corrcoef(np.roll(prof, i), c)[0, 1]
            if best is None or r > best[0]:
                best = (r, f"{names[i]} {q}")
    return best
print("global key", key_of(chroma.mean(axis=1)))
print("key by 15s window:")
for a in np.arange(0, dur, 15):
    m = (ct >= a) & (ct < a + 15)
    r, k = key_of(chroma[:, m].mean(axis=1))
    print(f"  {int(a)//60}:{int(a)%60:02d}  {k:8s} r={r:.2f}")

# --- 每秒：音量 dB、打擊樂比例、亮度、雜訊度（歡呼聲偏高）、低音比例、起音強度
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
rms_p = librosa.feature.rms(y=y_p, hop_length=hop)[0]
cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
flat = librosa.feature.spectral_flatness(y=y, hop_length=hop)[0]
S = np.abs(librosa.stft(y, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr)
low = S[freqs < 150].sum(axis=0) / (S.sum(axis=0) + 1e-9)
onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
ft = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
rows = []
for s in range(int(dur)):
    m = (ft >= s) & (ft < s + 1)
    db = 20 * np.log10(rms[m].mean() + 1e-9)
    rows.append(dict(t=s, db=round(float(db), 1),
                     perc=round(float(rms_p[m].mean() / (rms[m].mean() + 1e-9)), 2),
                     cent=int(cent[m].mean()), flat=round(float(flat[m].mean()), 3),
                     low=round(float(low[m].mean()), 3),
                     onset=round(float(onset[m[:len(onset)]].mean()), 2)))
json.dump(rows, open("persec.json", "w"), ensure_ascii=False)
print("per-5s summary: t  dB  perc  centroid  flatness  low  onset")
for a in range(0, int(dur), 5):
    g = rows[a:a + 5]
    f = lambda k: np.mean([r[k] for r in g])
    bar = "#" * max(0, int((f("db") + 40)))
    print(f"  {a//60}:{a%60:02d} {f('db'):6.1f} {f('perc'):.2f} {f('cent'):5.0f} {f('flat'):.3f} {f('low'):.3f} {f('onset'):.2f} {bar}")

# --- 自動段落切分（和聲＋音色，對齊拍點）
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
feat = np.vstack([librosa.util.normalize(chroma, axis=0), librosa.util.normalize(mfcc, axis=1)])
fs = librosa.util.sync(feat, beats, aggregate=np.median)
for k in (10, 14):
    bounds = librosa.segment.agglomerative(fs, k)
    times = [0.0] + [float(bt[b - 1]) if b > 0 else 0.0 for b in bounds[1:]]
    print(f"segments k={k}:", ", ".join(f"{int(t)//60}:{int(t)%60:02d}" for t in times))
