---
name: 時間軸分鏡腳本
description: 分析歌曲音訊（word-level 歌詞時間戳 + 音量能量曲線），產出切點對齊音樂的變動秒數 MV 分鏡表。當使用者提供歌曲要「做 MV 分鏡」「依歌曲分析做腳本」「分鏡表對齊歌詞」時使用
triggers: 時間軸分鏡、MV 腳本、歌曲分析分鏡、分鏡表、storyboard、依歌詞分鏡
version: 1.0.0
author: 羅東國小資訊組長
---

## 🎵 功能說明

不憑感覺切分鏡——先「聽」歌再下刀。用 Whisper word-level 時間戳拿到每句歌詞的精確起迄，用 ffmpeg 量測逐秒音量抓出能量結構（主歌/副歌/空拍/收尾），然後讓每個 cut 的切點對齊歌詞句子與音樂重點，產出變動秒數的分鏡表。

與 mv-04（九宮格分鏡）的分工：mv-04 管「一個角色的多視角視覺設計」，本技能管「整首歌的時間軸敘事結構」。兩者可搭配使用。

---

## 🚀 執行流程

### Step 1：word-level 歌詞轉錄

用全域 `audio-to-srt` 技能（Groq Whisper-large-v3-turbo）：

```bash
python "%USERPROFILE%/.claude/skills/audio-to-srt/scripts/transcribe_groq.py" "歌曲.mp3" --out _subtitles/歌曲.groq.json
```

產出的 JSON 含每個字的 start/end。**歌曲轉錄常見問題**（比口語嚴重，務必逐句校對）：
- 同音誤辨：憑上下文與「唱出來的音」推正字（例：未成全→圍成圈、小孩→笑還）
- 句頭漏辨：長間奏後的第一個字常被吃掉，比對兩次轉錄結果或用能量曲線補切點
- 長音：一個字拖好幾秒（如結尾的「淚」），時間戳會很長，是正常現象

### Step 2：能量曲線分析

```bash
ffmpeg -i "歌曲.mp3" -af "asetnsamples=44100,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-" -f null -
```

取每秒 RMS dB 值，判讀結構：
- **主歌**：低平（約 -18 dB 上下）
- **副歌**：注意是「高原」還是「山峰」——持續高能量的段落，畫面動作量要跟著撐住，不能中途放靜謐鏡頭
- **空拍**：人聲留白處是白閃/翻頁轉場的最佳落點
- **收尾**：人聲結束點決定淡出起點，尾奏通常很短

### Step 3：產出分鏡表

輸出 Markdown 檔（`storyboard_vN.md`），必含四個區塊：

1. **歌曲結構分析**：能量曲線表 + 關鍵發現（副歌形狀、空拍位置、人聲結束點）
2. **歌詞逐句時間戳**（校正版，供字幕檔用）
3. **分鏡表**：欄位固定為 `Cut | 時間 | 秒數 | 歌詞對應 | 畫面 | 動畫 | 進/出轉場`
   - 切點對齊歌詞句子邊界，秒數可變動（別硬切等長）
   - 白閃壓在「進副歌」與「空拍後第二波」兩個音樂重點上
   - 動畫欄用 zoom_in / zoom_out / pan_left / pan_right（對齊 make_mv.py 詞彙）
   - 轉場欄用 fadein / fade / whiteflash / fadeout
   - 秒數合計必須等於歌曲總長
4. **視覺設計原則**：色調軸線 + 能量對應動作量（副歌放人物動態、主歌收尾放靜物空景）

### Step 4：交付檢查

- [ ] 分鏡秒數加總 = 歌曲總長（ffprobe 驗證）
- [ ] 每個切點都能對應到歌詞句首或音樂事件
- [ ] 順手產出校對版 SRT（用 audio-to-srt 完整流程），字幕跟分鏡同源

---

## 📌 參考範例

`11_Opencode/mv_project/storyboard_v2.md`（寫實版）與 `storyboard_v3_creative.md`（塗鴉宇宙創意版）為本技能 SOP 的實際產出，含完整的能量判讀與切點設計案例。

## ⚠️ 風格提醒

分鏡的畫面設計若要用免費模型生圖，**勿用寫實風格**——優先抽象/風格化路線（塗鴉、粉筆、剪影），人物一致性靠統一媒材解決。詳見 mv-12（分鏡批次生圖）。
