---
name: 微電影聲音設計與混音
description: 為微電影 MV 製作口白配音（TTS＋ASR 驗字）、配置 CC0 環境音效（SFX），並用 FFmpeg 執行三軌閃避混音（Audio Ducking：口白期間自動壓低音樂）與雙層字幕（對白＋歌詞）分層。當使用者說「幫 MV 加口白」「配環境音」「微電影混音」「音樂閃避口白」時使用
triggers: 微電影混音、MV 口白、環境音效、SFX、Audio Ducking、雙層字幕、微電影聲音
version: 1.0.0
author: 羅東國小資訊組長
---

> 📏 **先讀《影片製作 6 項基本原則》**：`docs/影片製作基本原則.md`（01_MV製作 專案內，唯一正本，這裡不抄內容）。特別注意第 1 條（字幕帶淨空）與第 5 條（中文字級正確），對白字幕與歌詞字幕絕對不可互疊或遮擋重點畫面。

## 🔊 功能說明

純音樂 MV 只有一條歌曲音軌；但**微電影 MV** 之所以有電影感，關鍵在於**「三層聲音設計（歌曲＋口白＋環境音效）」**與**「雙層字幕設計（歌詞字幕＋劇情對白字幕）」**。

本技能承接 `mv-13`（微電影劇本）與 `mv-11`（時間軸分鏡表），在組裝成片（`make_mv.py`）階段，把口白、環境音與歌曲融合成一條廣播級（-15.5 LUFS）的立體音軌，並產出不打架的雙軌字幕。

---

## 🎧 三軌聲音設計規範

| 音軌 | 角色 | 音量與處理原則 |
|---|---|---|
| **Track 1：口白軌（Dialogue / VO）** | 主角獨白、間奏對話 | 最清晰優先。生成後去頭尾靜音，峰值控制在 -3 dBFS 左右。 |
| **Track 2：音樂軌（SUNO Music）** | 歌曲本體 | 正常段落滿格；**當 Track 1 有口白時，音樂自動壓低至 20%–30%（約 -10 ~ -14 dB，即 Audio Ducking）**，口白結束後 0.6 秒平順推回。若有片頭前導戲（Prologue），音樂延遲至 `prologue` 秒數後才進場。 |
| **Track 3：環境音軌（SFX / Ambience）** | 鐘聲、雨聲、翻書、腳步、海浪 | 只在轉場、片頭前導、間奏、片尾餘韻點綴（約 -18 ~ -24 dB），不蓋過人聲與副歌。優先使用專案 `assets/sfx/` 內的 CC0 音效庫。 |

---

## 🚀 執行流程

### Step 1：口白生成與 ASR 驗字（有口白時）

1. **台詞長度檢查**：對照分鏡表的口白區間，每秒不超過 **3.8 個中文字**（留呼吸感）。
2. **TTS 生成與挑選**：
   - 可使用本機或雲端 TTS（如 Edge-TTS 台灣語音 `zh-TW-HsiaoChenNeural` / `zh-TW-YunJheNeural`、BreezyVoice 或 ElevenLabs）。
   - **山獅霸防呆法**：重要獨白一次生成 3–5 個候選檔，跑一次 Whisper ASR 檢查有沒有念錯破音字，挑字音全對、停頓最自然的一版，存為 `outputs/<MV名>/audio/vo_cutNN.wav`。

### Step 2：環境音效（SFX）配置

對照分鏡表的 SFX 欄，從 CC0 音效庫挑選對應音檔，整理成音軌清單 `outputs/<MV名>/audio/audio_cues.json`（可直接餵給 `make_mv.py --audio-cues`）：

```json
{
  "prologue_sec": 6.0,
  "epilogue_sec": 4.0,
  "music_duck_volume": 0.22,
  "vo": [
    {"file": "audio/vo_prologue.wav", "start": 0.8, "gain_db": 0.0, "text": "如果那天沒有下雨，我們還會坐在一起嗎？"},
    {"file": "audio/vo_interlude.wav", "start": 64.5, "gain_db": 0.0, "text": "這給你，畢業後不准弄丟。"}
  ],
  "sfx": [
    {"file": "assets/sfx/school_bell.wav", "start": 0.0, "duration": 5.5, "gain_db": -12.0, "fade_out": 1.5},
    {"file": "assets/sfx/rain_light.wav", "start": 62.0, "duration": 8.0, "gain_db": -16.0, "fade_in": 1.0, "fade_out": 1.5}
  ]
}
```

### Step 3：FFmpeg 三軌閃避混音（Audio Ducking）＋ 兩段式響度

`make_mv.py --audio-cues` 內部會自動執行以下三步驟混音（也可手動用 FFmpeg 執行）：

1. **延遲音樂＋混入 SFX＋口白期間自動壓低音樂（Ducking）**：
   - 若有 `prologue_sec`（例如片頭演 6 秒才進歌），音樂用 `adelay=6000|6000` 往後推。
   - 口白區間 `[t_start - 0.3, t_end + 0.5]` 用 `volume='if(between(t,s,e), 0.22, 1.0)':eval=frame`（或 `sidechaincompress`）把音樂壓低，讓口白清清楚楚浮出來。
2. **兩段式響度標準化（-15.5 LUFS）**：
   - 混完總軌後，跑 `loudnorm=I=-15.5:TP=-1.5:LRA=11` → `ebur128` 量測實際值 → 補差額 → `alimiter=limit=0.72:level=false`（⚠️ 必加 `level=false`，否則靜音段與輕聲獨白會被硬拉爆音）。

### Step 4：雙層字幕規範（對白字幕 vs 歌詞字幕）

微電影同時有「角色講話」與「背景唱歌」，字幕若長一樣觀眾會分不清是誰在講話：

| 字幕類型 | 位置與樣式 | 時間軸規則 |
|---|---|---|
| **對白／口白字幕（Dialogue SRT）** | 畫面底部置中（MarginV 40）、白字黑邊、標準電影對白字級 | 嚴格對齊 `vo_cutNN.wav` 的起迄秒數 |
| **歌詞字幕（Lyrics SRT）** | 畫面底部偏上或左／右下角（或用暖黃／青色字區隔） | 若有 `prologue_sec`，整份歌詞 SRT 時間戳自動加上 `+prologue_sec` 平移；**口白出現期間，若有背景哼唱，不顯示歌詞字幕**，避免兩行字幕上下打架 |

---

## ✅ 交件前聲音與字幕自審清單

- [ ] **口白清晰度**：閉著眼睛聽，每一句口白都不會被歌聲或鼓點吃掉。
- [ ] **音樂進場點**：片頭前導戲（Prologue）接進歌曲第一個音時，情緒與畫面切點剛好對上。
- [ ] **無突兀截斷**：SFX 環境音進出都有 `afade`（0.5–1.5 秒淡入淡出），沒有像切菜一樣硬斷。
- [ ] **字幕不打架**：同一秒畫面上最多只有一種字幕，且完全遵守《影片製作 6 項基本原則》第 1 條（字幕帶淨空）。
- [ ] **整體響度**：成片 `ebur128` 落在 `-15.5 ± 0.5 LUFS`，True Peak `≤ -2.0 dBFS`。
