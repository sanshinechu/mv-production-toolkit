"""粗略拆出主旋律線（人聲／獨奏），看它每段有多突出、唱在哪個音域。

用法：
    uv run --with librosa python vocal.py 歌曲.mp3

⚠️ 用的是 REPET-SIM（把「重複的伴奏」扣掉，剩下的當主旋律），不是專業人聲分離，
   吉他旋律也會被算進來。數字拿來看趨勢（哪段變突出、哪段唱最高），別當精確值。
"""
import sys
import numpy as np
import librosa

sys.stdout.reconfigure(encoding="utf-8")
y, sr = librosa.load(sys.argv[1], sr=22050, mono=True)
dur = len(y) / sr
hop = 512
S_full, phase = librosa.magphase(librosa.stft(y, hop_length=hop))
S_filter = librosa.decompose.nn_filter(S_full, aggregate=np.median, metric="cosine",
                                       width=int(librosa.time_to_frames(2, sr=sr, hop_length=hop)))
S_filter = np.minimum(S_full, S_filter)
mask_v = librosa.util.softmask(S_full - S_filter, 10 * S_filter, power=2)
S_fg = mask_v * S_full

freqs = librosa.fft_frequencies(sr=sr)
band = (freqs > 180) & (freqs < 4000)
fg = S_fg[band].sum(axis=0)
tot = S_full[band].sum(axis=0) + 1e-9
t = librosa.frames_to_time(np.arange(S_full.shape[1]), sr=sr, hop_length=hop)

print("t     主旋律占比")
for a in range(0, int(dur), 3):
    m = (t >= a) & (t < a + 3)
    share = fg[m].sum() / tot[m].sum()
    print(f"{a//60}:{a%60:02d}  {share:5.2f}  " + "#" * int(share * 60))

yv = librosa.istft(S_fg * phase, hop_length=hop)
f0, vflag, vprob = librosa.pyin(yv, fmin=150, fmax=1100, sr=sr, hop_length=hop)
tt = librosa.times_like(f0, sr=sr, hop_length=hop)
print("\n主旋律音高（中位數／前 10% 高音）每 15 秒")
for a in range(0, int(dur), 15):
    m = (tt >= a) & (tt < a + 15) & vflag & (vprob > 0.5)
    if m.sum() > 20:
        med, hi = np.median(f0[m]), np.percentile(f0[m], 90)
        print(f"{a//60}:{a%60:02d}  median {librosa.hz_to_note(med)}  p90 {librosa.hz_to_note(hi)}")
    else:
        print(f"{a//60}:{a%60:02d}  (主旋律很少)")
