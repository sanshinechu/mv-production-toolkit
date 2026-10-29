# -*- coding: utf-8 -*-
r"""《半張車票》環境音與音效合成：15 支 wav，純 numpy／scipy 合成，不用素材庫。

用法（cmd）：
  python scripts/build_half_ticket_sfx.py --project outputs/半張車票     # 相對路徑：以 01_MV製作 為基準
  python scripts/build_half_ticket_sfx.py --project <當台封存區>\半張車票  # 絕對路徑：專案已搬到當台封存區時

- 音效寫到 <專案>/audio/，檔名與 prepare_audio_cues_and_subs.py 的 SFX_PLAN 對齊。
- 路徑不寫死：各機碟號不同，而且專案上架後還會搬到當台封存區（見 docs/影片分流策略.md）。
"""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 參數解析刻意排在第三方 import 前面：沒裝 soundfile 的機器也要能跑 --help、
# 也才會先看到路徑的錯誤而不是 ModuleNotFoundError。
_ap = argparse.ArgumentParser(description="《半張車票》環境音與音效合成")
_ap.add_argument("--project", required=True,
                 help=r"專案資料夾：絕對路徑，或相對於 01_MV製作（例如 outputs\半張車票）")
_args = _ap.parse_args()
_project = Path(_args.project)
if not _project.is_absolute():
    _project = ROOT / _project
OUT_DIR = str(_project / "audio")

import numpy as np
import scipy.signal as signal
import soundfile as sf

SR = 48000
os.makedirs(OUT_DIR, exist_ok=True)
print(f"[DIR] 音效輸出到 {OUT_DIR}")

def norm(x, peak_db=-3.0):
    pk = np.max(np.abs(x))
    if pk > 0:
        target = 10 ** (peak_db / 20.0)
        return (x / pk) * target
    return x

def fade(x, in_sec=0.1, out_sec=0.1):
    n_in = int(in_sec * SR)
    n_out = int(out_sec * SR)
    res = x.copy()
    if n_in > 0 and n_in < len(res):
        res[:n_in] *= np.linspace(0, 1, n_in)
    if n_out > 0 and n_out < len(res):
        res[-n_out:] *= np.linspace(1, 0, n_out)
    return res

# 1. 大雨 + 雨刷 + 引擎低鳴 (Prologue 24s)
def gen_rain_wiper_engine(dur=24.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    # Rain (pink noise)
    white = np.random.randn(n)
    b, a = signal.butter(2, [300 / (SR / 2), 4000 / (SR / 2)], btype='band')
    rain = signal.lfilter(b, a, white)
    # Droplets
    drops = np.zeros(n)
    drop_indices = np.random.choice(n, size=int(dur * 40), replace=False)
    drops[drop_indices] = np.random.uniform(0.5, 1.5, size=len(drop_indices))
    b_d, a_d = signal.butter(2, [1200 / (SR / 2), 3500 / (SR / 2)], btype='band')
    drops = signal.lfilter(b_d, a_d, drops)
    rain = rain * 0.7 + drops * 0.3
    
    # Engine idle (55 Hz + harmonics)
    eng = (np.sin(2 * np.pi * 55 * t) * 0.6 +
           np.sin(2 * np.pi * 110 * t) * 0.3 +
           np.sin(2 * np.pi * 165 * t) * 0.15)
    b_e, a_e = signal.butter(2, 250 / (SR / 2), btype='low')
    eng = signal.lfilter(b_e, a_e, eng)
    # Modulate engine slightly
    eng *= (1.0 + 0.1 * np.sin(2 * np.pi * 3.5 * t))
    
    # Wiper squeak (period 1.8s: wipe left, wipe right)
    wiper = np.zeros(n)
    period = 1.8
    for st in np.arange(0.5, dur - 1.0, period):
        idx = int(st * SR)
        w_len = int(0.35 * SR)
        if idx + w_len < n:
            wt = np.linspace(0, 0.35, w_len)
            sweep = np.sin(2 * np.pi * (800 + 400 * np.sin(np.pi * wt / 0.35)) * wt)
            friction = signal.lfilter(b, a, np.random.randn(w_len)) * 0.5
            w_snd = (sweep * 0.3 + friction * 0.7) * np.sin(np.pi * wt / 0.35) ** 2
            wiper[idx:idx + w_len] += w_snd
            
    mix = rain * 0.6 + eng * 0.35 + wiper * 0.25
    return norm(fade(mix, 0.5, 1.0))

# 2. 煞車潑水聲 (8s)
def gen_brake_splash(dur=8.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    # Brake squeal around 2.0s to 4.5s
    squeal = np.zeros(n)
    st, en = int(1.5 * SR), int(4.5 * SR)
    sq_t = t[st:en] - 1.5
    freq = 2400 - 300 * (sq_t / 3.0)
    sq_snd = np.sin(2 * np.pi * freq * sq_t) * (1.0 + 0.3 * np.sin(2 * np.pi * 40 * sq_t))
    sq_env = np.sin(np.pi * sq_t / 3.0) ** 1.5
    squeal[st:en] = sq_snd * sq_env * 0.4
    
    # Water splash (3.0s to 5.5s)
    splash = np.zeros(n)
    sp_st, sp_en = int(2.8 * SR), int(5.5 * SR)
    sp_n = sp_en - sp_st
    white = np.random.randn(sp_n)
    b, a = signal.butter(2, [400 / (SR / 2), 2500 / (SR / 2)], btype='band')
    sp_snd = signal.lfilter(b, a, white)
    sp_env = np.sin(np.pi * np.linspace(0, 1, sp_n)) ** 2
    splash[sp_st:sp_en] = sp_snd * sp_env * 0.6
    
    mix = squeal + splash
    return norm(fade(mix, 0.2, 0.5))

# 3. 雨打傘面 + 踩水急奔 (8s)
def gen_umbrella_steps(dur=8.0):
    n = int(dur * SR)
    # Rain on umbrella (patter)
    white = np.random.randn(n)
    b, a = signal.butter(2, [800 / (SR / 2), 3000 / (SR / 2)], btype='band')
    pat = signal.lfilter(b, a, white) * 0.4
    # Footsteps splashing every 0.6s
    steps = np.zeros(n)
    for st in np.arange(1.0, 7.0, 0.65):
        idx = int(st * SR)
        flen = int(0.2 * SR)
        if idx + flen < n:
            ft = np.linspace(0, 1, flen)
            thud = np.sin(2 * np.pi * 80 * ft) * np.exp(-15 * ft)
            spl = signal.lfilter(b, a, np.random.randn(flen)) * np.exp(-12 * ft)
            steps[idx:idx + flen] += (thud * 0.6 + spl * 0.5)
    mix = pat + steps
    return norm(fade(mix, 0.3, 0.5))

# 4. 車庫電流 + 對講機微雜訊 (16s)
def gen_garage_ambient(dur=16.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    # 60Hz hum + 120Hz harmonic (fluorescent lamp ballast)
    hum = np.sin(2 * np.pi * 60 * t) * 0.4 + np.sin(2 * np.pi * 120 * t) * 0.25 + np.sin(2 * np.pi * 180 * t) * 0.1
    b, a = signal.butter(2, 400 / (SR / 2), btype='low')
    hum = signal.lfilter(b, a, hum) * 0.3
    # Distant rain background
    rain = signal.lfilter(*signal.butter(2, 800 / (SR / 2), btype='low'), np.random.randn(n)) * 0.15
    # Occasional radio squelch around 6s and 12s
    squelch = np.zeros(n)
    for q in [5.5, 12.0]:
        idx = int(q * SR)
        q_len = int(0.25 * SR)
        if idx + q_len < n:
            b_q, a_q = signal.butter(2, [1000 / (SR / 2), 3000 / (SR / 2)], btype='band')
            sq_burst = signal.lfilter(b_q, a_q, np.random.randn(q_len)) * np.sin(np.pi * np.linspace(0, 1, q_len))
            squelch[idx:idx + q_len] += sq_burst * 0.35
    mix = hum + rain + squelch
    return norm(fade(mix, 0.5, 0.5))

# 5. 原子筆寫字 + 皮鞋腳步 (8s)
def gen_pen_footsteps(dur=8.0):
    n = int(dur * SR)
    # Pen scratching (0.8s to 4.5s)
    pen = np.zeros(n)
    p_st, p_en = int(1.0 * SR), int(4.5 * SR)
    p_len = p_en - p_st
    white = np.random.randn(p_len)
    b, a = signal.butter(2, [1500 / (SR / 2), 6000 / (SR / 2)], btype='band')
    scratch = signal.lfilter(b, a, white)
    # modulate scratching in strokes
    t_p = np.linspace(0, 3.5, p_len)
    stroke_mod = (np.sin(2 * np.pi * 4 * t_p) ** 4) * np.exp(-0.1 * t_p)
    pen[p_st:p_en] = scratch * stroke_mod * 0.5
    # Leather shoes walking away (4.5s to 7.5s)
    walk = np.zeros(n)
    for st in [4.8, 5.6, 6.4, 7.2]:
        idx = int(st * SR)
        flen = int(0.18 * SR)
        if idx + flen < n:
            ft = np.linspace(0, 1, flen)
            step = (np.sin(2 * np.pi * 120 * ft) * 0.5 + np.random.randn(flen) * 0.2) * np.exp(-20 * ft)
            walk[idx:idx + flen] += step
    mix = pen + walk
    return norm(fade(mix, 0.2, 0.4))

# 6. 打開鐵盒蓋金屬摩擦 (4s)
def gen_tin_box(dur=4.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    # Lid slides and opens around 1.2s to 2.2s
    box = np.zeros(n)
    idx = int(1.0 * SR)
    blen = int(1.0 * SR)
    bt = np.linspace(0, 1.0, blen)
    # scrape + metallic ringing resonance
    scrape = signal.lfilter(*signal.butter(2, [1800 / (SR / 2), 5000 / (SR / 2)], btype='band'), np.random.randn(blen))
    ring = np.sin(2 * np.pi * 1350 * bt) * np.exp(-4 * bt) + np.sin(2 * np.pi * 2100 * bt) * np.exp(-6 * bt)
    clack = np.sin(2 * np.pi * 600 * bt) * np.exp(-25 * bt)
    box[idx:idx + blen] = (scrape * 0.4 * np.sin(np.pi * bt) + ring * 0.4 + clack * 0.5)
    return norm(fade(box, 0.1, 0.3))

# 7. 輕撕車票 (2s)
def gen_ticket_tear(dur=2.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    tear = np.zeros(n)
    idx = int(0.4 * SR)
    tlen = int(0.45 * SR)
    tt = np.linspace(0, 0.45, tlen)
    b, a = signal.butter(2, [1200 / (SR / 2), 6500 / (SR / 2)], btype='band')
    noise = signal.lfilter(b, a, np.random.randn(tlen))
    env = (np.sin(np.pi * tt / 0.45) ** 2) * (1.0 + 0.4 * np.sin(2 * np.pi * 35 * tt))
    tear[idx:idx + tlen] = noise * env
    return norm(fade(tear, 0.05, 0.1))

# 8. 引擎點火發動 (3s)
def gen_engine_start(dur=3.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    snd = np.zeros(n)
    # Starter cranking (0.3s to 1.5s)
    idx_s, idx_e = int(0.3 * SR), int(1.5 * SR)
    c_len = idx_e - idx_s
    c_t = np.linspace(0, 1.2, c_len)
    crank = np.sin(2 * np.pi * (8 + 4 * c_t) * c_t) * np.sin(2 * np.pi * 180 * c_t)
    snd[idx_s:idx_e] += crank * 0.4
    # Engine catch and roar (1.3s to 3.0s)
    i_s = int(1.3 * SR)
    r_len = n - i_s
    rt = np.linspace(0, (n - i_s) / SR, r_len)
    roar = (np.sin(2 * np.pi * 70 * rt) * 0.6 + np.sin(2 * np.pi * 140 * rt) * 0.3 + np.sin(2 * np.pi * 210 * rt) * 0.2)
    roar *= np.exp(-1.5 * rt) * 1.5 + 0.5
    b, a = signal.butter(2, 350 / (SR / 2), btype='low')
    roar = signal.lfilter(b, a, roar)
    snd[i_s:] += roar * 0.6
    return norm(fade(snd, 0.1, 0.3))

# 9. 公車氣壓開門聲 (3s)
def gen_door_air(dur=3.0):
    n = int(dur * SR)
    snd = np.zeros(n)
    # Air release "PSSSH" (0.2s to 1.4s)
    idx = int(0.2 * SR)
    alen = int(1.2 * SR)
    at = np.linspace(0, 1.2, alen)
    b, a = signal.butter(2, [800 / (SR / 2), 4500 / (SR / 2)], btype='band')
    pssh = signal.lfilter(b, a, np.random.randn(alen)) * (np.exp(-3 * at) * 0.8 + 0.1)
    # Door mechanism clack at 0.9s
    clack_idx = int(0.9 * SR)
    clen = int(0.15 * SR)
    ct = np.linspace(0, 0.15, clen)
    clack = np.sin(2 * np.pi * 320 * ct) * np.exp(-30 * ct) + signal.lfilter(b, a, np.random.randn(clen)) * np.exp(-25 * ct)
    snd[idx:idx + alen] += pssh * 0.7
    snd[clack_idx:clack_idx + clen] += clack * 0.5
    return norm(fade(snd, 0.05, 0.2))

# 10. 鑰匙掛上小鈴鐺聲 (3s)
def gen_key_bell(dur=3.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    snd = np.zeros(n)
    idx = int(0.3 * SR)
    blen = n - idx
    bt = np.linspace(0, blen / SR, blen)
    # Small bell chime 2800 Hz + 3500 Hz with shimmer
    bell = (np.sin(2 * np.pi * 2800 * bt) * 0.6 +
            np.sin(2 * np.pi * 3520 * bt) * 0.4 +
            np.sin(2 * np.pi * 5600 * bt) * 0.15) * np.exp(-3.5 * bt)
    # Key clink transient
    clink = signal.lfilter(*signal.butter(2, [2000 / (SR / 2), 7000 / (SR / 2)], btype='band'), np.random.randn(blen)) * np.exp(-30 * bt)
    snd[idx:] = bell * 0.6 + clink * 0.4
    return norm(fade(snd, 0.02, 0.3))

# 11. 鐵捲門拉起 (3.5s)
def gen_shutter(dur=3.5):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    # Metal slats rolling & chain rumble
    white = np.random.randn(n)
    b, a = signal.butter(2, [250 / (SR / 2), 2200 / (SR / 2)], btype='band')
    rumble = signal.lfilter(b, a, white)
    # Slat clatter modulation
    clatter = (np.sin(2 * np.pi * 14 * t) ** 2) * 0.4 + 0.6
    snd = rumble * clatter * np.sin(np.pi * t / dur)
    return norm(fade(snd, 0.2, 0.4))

# 12. 早市麻雀鳥鳴 + 晨光環境 (22s)
def gen_morning_market(dur=22.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    snd = np.zeros(n)
    # Sparrow chirps at random intervals
    chirp_times = [1.2, 2.5, 4.0, 7.5, 9.2, 12.0, 14.8, 17.5, 20.0]
    for ct in chirp_times:
        idx = int(ct * SR)
        clen = int(0.22 * SR)
        if idx + clen < n:
            c_t = np.linspace(0, 0.22, clen)
            freq = 3200 + 1200 * np.sin(2 * np.pi * 7 * c_t)
            c_snd = np.sin(2 * np.pi * freq * c_t) * (np.sin(np.pi * c_t / 0.22) ** 2)
            snd[idx:idx + clen] += c_snd * 0.35
            
    # Gentle distant market murmur (filtered low-mid noise)
    b, a = signal.butter(2, [300 / (SR / 2), 1800 / (SR / 2)], btype='band')
    market = signal.lfilter(b, a, np.random.randn(n)) * 0.12
    snd += market
    return norm(fade(snd, 0.5, 1.0))

# 13. 公車到站提示音 Ding-Dong (4s)
def gen_bus_chime(dur=4.0):
    n = int(dur * SR)
    snd = np.zeros(n)
    # Ding (659.25 Hz - E5) at 0.5s
    st1 = int(0.5 * SR)
    l1 = int(1.2 * SR)
    t1 = np.linspace(0, 1.2, l1)
    chime1 = (np.sin(2 * np.pi * 659.25 * t1) + 0.3 * np.sin(2 * np.pi * 1318.5 * t1)) * np.exp(-3.0 * t1)
    snd[st1:st1 + l1] += chime1 * 0.6
    # Dong (523.25 Hz - C5) at 1.4s
    st2 = int(1.4 * SR)
    l2 = int(1.5 * SR)
    t2 = np.linspace(0, 1.5, l2)
    chime2 = (np.sin(2 * np.pi * 523.25 * t2) + 0.3 * np.sin(2 * np.pi * 1046.5 * t2)) * np.exp(-2.5 * t2)
    snd[st2:st2 + l2] += chime2 * 0.6
    return norm(fade(snd, 0.05, 0.5))

# 14. 悠遊卡刷卡嗶聲 (3s)
def gen_card_beep(dur=3.0):
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    snd = np.zeros(n)
    # Beep at 0.5s, 1760 Hz (A6), 0.12s
    idx = int(0.5 * SR)
    blen = int(0.12 * SR)
    bt = np.linspace(0, 0.12, blen)
    beep = np.sin(2 * np.pi * 1760 * bt) * np.sin(np.pi * bt / 0.12)
    snd[idx:idx + blen] = beep * 0.6
    # Smooth modern bus interior hum
    b_h, a_h = signal.butter(2, 200 / (SR / 2), btype='low')
    hum = signal.lfilter(b_h, a_h, np.random.randn(n)) * 0.1
    snd += hum
    return norm(fade(snd, 0.1, 0.5))

sfx_generators = [
    ("sfx_01_rain_wiper_engine.wav", gen_rain_wiper_engine, 24.0),
    ("sfx_02_brake_splash.wav", gen_brake_splash, 8.0),
    ("sfx_03_footsteps_water.wav", gen_umbrella_steps, 8.0),
    ("sfx_04_garage_ambient.wav", gen_garage_ambient, 16.0),
    ("sfx_05_writing_footsteps.wav", gen_pen_footsteps, 8.0),
    ("sfx_06_tin_box.wav", gen_tin_box, 4.0),
    ("sfx_07_ticket_tear.wav", gen_ticket_tear, 2.0),
    ("sfx_08_engine_start.wav", gen_engine_start, 3.0),
    ("sfx_09_door_air.wav", gen_door_air, 3.0),
    ("sfx_10_key_bell.wav", gen_key_bell, 3.0),
    ("sfx_11_shutter_open.wav", gen_shutter, 3.5),
    ("sfx_12_morning_market.wav", gen_morning_market, 22.0),
    ("sfx_13_rain_return.wav", gen_rain_wiper_engine, 15.0),
    ("sfx_14_bus_chime.wav", gen_bus_chime, 4.0),
    ("sfx_15_card_beep.wav", gen_card_beep, 3.0),
]

for fname, gen_func, dur in sfx_generators:
    wav = gen_func(dur)
    out_path = os.path.join(OUT_DIR, fname)
    sf.write(out_path, wav, SR)
    print(f"[OK] Generated {fname} ({dur}s)")
