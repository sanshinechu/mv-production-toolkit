"""畫頻譜圖，用「看」的判讀樂器進出、人聲、歡呼聲。

用法：
    uv run --with librosa --with matplotlib python spec.py 歌曲.mp3
    uv run --with librosa --with matplotlib python spec.py 歌曲.mp3 236-276 276-318

不給區段就只畫全曲；區段用「起秒-迄秒」，一段一張圖。

怎麼看：
- 橫向的亮線＝持續的音（人聲、吉他、低音）；線條呈波浪＝顫音
- 直向的亮線＝鼓或重拍
- 1 kHz 附近一團霧狀、沒有線條的亮區＝觀眾歡呼／掌聲
- 高頻（2 kHz 以上）整片變暗＝樂團停下來或抽空
"""
import sys
import numpy as np
import librosa, librosa.display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

path = sys.argv[1]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr

def spec(a, b, name, fmax=8000):
    seg = y[int(a * sr):int(b * sr)]
    S = librosa.amplitude_to_db(np.abs(librosa.stft(seg, n_fft=2048, hop_length=256)), ref=np.max)
    fig, ax = plt.subplots(figsize=(16, 5))
    librosa.display.specshow(S, sr=sr, hop_length=256, x_axis="time", y_axis="log", ax=ax, cmap="magma")
    ax.set_ylim(40, fmax)
    ticks = np.arange(0, b - a + 0.01, 2 if b - a <= 40 else 10)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{int(a+t)//60}:{int(a+t)%60:02d}" for t in ticks], fontsize=7)
    ax.set_title(name)
    fig.tight_layout()
    fig.savefig(f"{name}.png", dpi=70)
    plt.close(fig)

spec(0, dur, "full")
for arg in sys.argv[2:]:
    a, b = (float(x) for x in arg.split("-"))
    spec(a, b, f"spec_{int(a)}-{int(b)}")
