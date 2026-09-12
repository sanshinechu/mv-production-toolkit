---
title: 保留原旋律的曲風改編（私人使用）
date: 2026-09-12
machine: 家裡用筆電
tags:
  - MV製作
  - Suno
  - 編曲分析
  - 翻唱
---

# 保留原旋律的曲風改編

把喜歡的歌換成搖滾現場／爵士／Lo-Fi，**旋律照舊，一聽就知道是原曲**。

姊妹篇 [參考曲分析：至少還有你](../參考曲分析_至少還有你搖滾現場版/README.md) 解決的是
「怎麼寫出好的編排」；這份解決的是「怎麼把原曲的旋律保下來」。兩份搭著用。

> ⚠️ **這份文件的前提是「只有自己聽」。** 成品不要公開、不要給學生或同事、
> **絕對不要上傳教學頻道**。理由見第九節，那節請務必讀完。

---

## 一、上次為什麼被擋

2026-09-11 想把《白色風車》做成搖滾現場版，Suno 直接擋下。當時以為是「Suno 不給做翻唱」，
其實不是——Suno 有**兩道各自獨立**的閘門，那次兩道都撞上：

| 閘門 | 擋什麼 | 為什麼會中 |
|---|---|---|
| **音訊指紋** | 上傳的音檔拿去比對商業母帶資料庫 | 直接傳原曲 MP3 → 必中 |
| **歌詞比對** | 貼上的歌詞文字比對知名歌詞庫 | 貼原曲歌詞 → 必中 |

**關鍵在這裡：兩道閘門擋的都不是旋律。** 指紋比對的是「哪一版錄音」，
旋律本身沒有指紋可比對。所以只要餵它一份**自己合成、不存在於任何資料庫的旋律音軌**，
Cover 功能就會正常運作。

> ✅ **2026-09-12 實證確認。** 拿《至少還有你》抽出旋律、合成成鋼琴導引音軌上傳，
> **Suno 正常收下並成功 Cover，成品好聽且旋律認得出來**。
> 這句話昨天寫的時候只是推論，現在有證據了。

而這正是 Suno Cover 官方設計的用法——官方說法是「30 秒哼唱就夠」。
不會哼也不會彈沒關係，讓程式代勞就好。這不是鑽漏洞，是照著功能的設計意圖用。

> 🚫 **不做的事**：改錯字、同音字這類繞過歌詞過濾的方法。違反 Suno 條款、
> 帳號可能被停，而且歌詞仍然是別人的。這條紅線 9/11 畫過一次，沿用。

---

## 二、整條流程

```
原曲.mp3（自己合法持有的）
   │
   ├─ 路線 A（首選）：網路找現成 MIDI／卡拉 OK 檔
   │                  人工編的比 AI 抽的準太多，直接跳到第三步
   │
   └─ 路線 B（找不到 MIDI 才走）：
        extract_melody.py
        Demucs 分離人聲 → Basic Pitch 抽音符 → melody.mid
   │
   ▼
make_guide.py
合成導引音軌 guide.wav（單音旋律 ＋ 節拍 click）
   ← 程式產生的，沒有商業母帶指紋，指紋閘門抓不到
   ▼
Suno → 上傳 guide.wav → ⋯ 選單 → Cover → 填新的 Style 描述
   ▼
analyze.py 驗收編排有沒有做出來
```

素材全部放暫存區或 `素材/`，**不進 git**（同資料夾的 `.gitignore` 已經釘死）。

---

## 三、路線 A：找現成 MIDI（首選）

華語流行歌的 MIDI 在卡拉 OK 圈流通得很廣，搜「歌名 + MIDI」或「歌名 + 伴奏 midi」多半找得到。
人工編的 MIDI 音準和節奏都遠勝 AI 抽取，**能找到就一定走這條**，省掉 Demucs 那幾 GB 的下載。

拿到 `.mid` 或 `.kar` 直接跳第五節。

---

## 四、路線 B：從原曲抽旋律

```bash
uv run --python 3.10 --with demucs --with basic-pitch python 腳本/extract_melody.py "原曲.mp3"
```

做兩件事：Demucs 把人聲從伴奏裡拆出來，Basic Pitch 再把人聲轉成音符。

**幾個坑先講**：

- **Python 一定要釘 3.10**。Basic Pitch 官方只支援到 3.10，這台預設的 3.14 會裝不起來。
  `uv run --python 3.10` 會自己抓一份 3.10，不影響系統的 Python
- **第一次跑要下載好幾 GB**（torch ＋ Demucs 模型），泡杯茶。之後有快取就快
- 腳本預設會把**和弦壓成單音**。導引音軌是單音旋律，和弦反而會讓 Suno 抓錯重點。
  要保留和弦加 `--keep-polyphonic`
- 預設會濾掉**高八度的幽靈音**。音高偵測器很容易把泛音誤判成獨立的音，
  症狀是每個音的尾巴多出一個小聲的高八度。真的有高八度和聲時加 `--keep-ghosts` 關掉
- 也預設清掉 Basic Pitch 塞的**彎音（pitch bend）**，不清的話合成出來會走音
- 抽出來的是「差不多」的旋律，不是樂譜。導引音軌只需要音高輪廓，夠用就好

手上已經是乾淨的人聲軌或單音演奏 → 加 `--skip-demucs` 跳過分離。

---

## 五、合成導引音軌

先量原曲 BPM（**這步不要跳過**，理由見下）：

```bash
uv run --with librosa python ../參考曲分析_至少還有你搖滾現場版/分析腳本/analyze.py "原曲.mp3"
```

看 `global tempo` 那行，然後：

```bash
uv run --python 3.10 --with pretty_midi --with soundfile python 腳本/make_guide.py "原曲_melody.mid" --bpm 123
```

產出 `原曲_melody_guide.wav`。**難聽是正常的**，它的任務只有三個：

1. 音高輪廓在 → Suno Cover 靠這個保住原旋律
2. 拍子清楚 → 腳本會加一條 click 軌踩在拍點上。**這是成敗關鍵**，
   少了它 Suno 常常抓不準速度，整首會歪
3. 不是任何商業錄音 → 沒有母帶指紋可比對

### ⚠️ 關於 BPM 的一個常見誤解

網路上常看到「Basic Pitch 輸出固定是 120 BPM，要縮放回原曲速度」。
**這句話只對一半，照做反而會弄壞。**

Basic Pitch 寫進 MIDI 的**速度標記**確實固定是 120，但音符的**秒數是對的**
（跟原曲對得上）。所以：

- 直接合成成 WAV → **旋律時間完全正確，不需要伸縮**
- 匯進 DAW 對格線 → 才會因為速度標記錯掉而對不上

`--bpm` 在這支腳本裡**只影響 click 軌打在哪裡**，但還是一定要給對，
不然 click 會跟旋律打架，反而害 Suno 抓錯。真的想改變速度請用 `--stretch`。

其他好用的參數：

| 參數 | 用途 |
|---|---|
| `--max-sec 120` | Suno 上傳有長度上限，太長就截一段最有代表性的（通常是副歌前後） |
| `--transpose -2` | 移調。原唱太高唱不上去的感覺，降個 2 到 3 個半音 |
| `--no-click` | MIDI 本身節奏已經很清楚時可以關掉 |
| `--click-level 0.3` | click 太小聲抓不到、太大聲蓋過旋律，預設 0.22 |

---

## 六、Suno Cover 怎麼填

上傳 `guide.wav` → 在那個 clip 的 **⋯ 選單選 Cover** → 填 Style 和歌詞。

### Style：寫「目的地」，不要寫「修改指令」

最常見的失敗是寫成 `make it rock`。要**完整描述你要的那支樂團**，
Suno 才知道往哪走。五個要素一個都不要少：**曲風、情緒、人聲、樂器、製作感＋BPM**。

**搖滾現場版**（直接沿用[參考曲分析第六節](../參考曲分析_至少還有你搖滾現場版/README.md)驗過的範本）：

> Live rock concert recording of a Mandopop ballad, 123 BPM, female lead vocal starting restrained in a low register and building to powerful belted high notes, arena reverb, crowd cheering at the start and end, overdriven electric guitars with melodic lead lines, driving live drums, warm bass, gradual build-up across the song, dramatic band stop before the final chorus, stripped-down quiet breakdown then full-band explosive last chorus, big sustained ending with applause.

**爵士酒吧版**：

> Intimate late-night jazz club recording of a Mandopop ballad, around 90 BPM with a relaxed swing feel, smoky female vocal with loose behind-the-beat phrasing, brushed drums, upright double bass walking lines, warm Rhodes electric piano and soft comping guitar, muted trumpet answering the vocal phrases, tasteful piano solo in the middle, room tone and quiet glasses in the background, warm analog tape warmth, gentle ritardando ending.

**Lo-Fi 治癒版**：

> Lo-fi hip hop reinterpretation of a Mandopop ballad, around 75 BPM, soft breathy female vocal mixed low and intimate, dusty boom-bap drums with light vinyl crackle, mellow Rhodes chords, warm sub bass, occasional rain and distant city ambience, tape saturation and gentle wow-and-flutter, unhurried and nostalgic, simple loop-based arrangement, fades out gently.

**Bossa Nova 版**：

> Bossa nova version of a Mandopop love song, around 100 BPM, soft close-miked male vocal singing gently and almost whispered, classic nylon-string guitar with syncopated bossa comping, brushed snare and rim clicks, subtle upright bass, light flute or soft saxophone countermelody, warm 1960s Brazilian studio sound, relaxed and sunny, gentle ending on a sustained chord.

範本裡的 BPM 記得換成你用 analyze.py 量出來的數字。

### 歌詞欄：三選一

| 做法 | 會不會被擋 | 適合 |
|---|---|---|
| 填 `[Instrumental]` | 不會 | **最乾淨**。曲風轉換的效果照樣百分之百聽得出來 |
| 自己寫新詞（旋律照舊） | 不會 | 想要人聲。等於「改詞翻唱」，詞是你自己的 |
| 貼原詞 | **會被擋** | Suno 走不通，只能改走第八節的本地方案 |

> 🔴 **2026-09-12 實證：《至少還有你》的原詞一樣被擋。**
> 9/11 只測過《白色風車》，當時以為可能是杰威爾管得特別嚴、別家未必收錄。
> 實際上滾石這首照樣擋。**不要再抱著「換一首也許就過了」的期待去試。**

自己填新詞時，照原旋律的字數斷句寫，貼合度會好很多。
結構標籤（`[Verse]`、`[Chorus]`、`[Break, band stops]` 之類）照
[參考曲分析第六節](../參考曲分析_至少還有你搖滾現場版/README.md)的範本走。

### 生成與挑選

- 同設定**生 4～6 首再挑**，Agroce 同一首也做了兩種風格
- 第一次先**不要動歌詞**，單純聽曲風換得成不成功，一次只變一個變數
- 挑的時候**先聽急停那一段**，那裡最能看出成不成功

---

## 七、驗收

拿成品跑同一套分析，跟原曲對照：

```bash
uv run --with librosa python ../參考曲分析_至少還有你搖滾現場版/分析腳本/analyze.py 成品.mp3
uv run --with librosa --with matplotlib python ../參考曲分析_至少還有你搖滾現場版/分析腳本/spec.py 成品.mp3 236-276
```

該看什麼：

- **BPM** 跟原曲差不多（差太多代表 click 沒發揮作用，或 Suno 自己改了速度）
- **調性**跟原曲一致（除非你有下 `--transpose`）
- **能量曲線逐段往上爬**，主歌到最後副歌應該一路變大
- 有下急停／抽空標籤的話，那幾個時間點應該看得到明顯的 dB 掉落

---

## 八、備援：本地 ACE-Step（完全離線）

Suno 還是不配合、或就是想用原詞的話走這條。**這台的 RTX 4060 跑得動**
（ACE-Step 1.5 官方說不到 4GB VRAM）。

沒有雲端的事前審查，原詞也能跑。**而且在法律上是最乾淨的一條**：
著作權法第 51 條的條件是「個人或家庭非營利目的，在合理範圍內，
利用圖書館及**非供公眾使用之機器**」——家裡的筆電符合這個條件，
把音檔傳到 Suno 雲端嚴格講站不太住腳。

代價是要自己裝環境、效果和易用性都不如 Suno。真的走這條再來處理。

---

## 九、邊界：為什麼別人放得上 YouTube，你不要

B 站 Agroce 那批搖滾現場版被搬到 YouTube，[有一支 22 萬觀看](https://www.youtube.com/watch?v=LMTUJ0PrkKQ)，
2026-09-12 確認還在線上。既然人家放得上去，為什麼這份文件一直叫你不要公開？

因為這裡有**三套互不相干的標準**被混在一起了：

| | 誰在判 | 什麼時候判 | 鬆緊 |
|---|---|---|---|
| **Suno 過濾** | 平台自保 | 事前，按下生成前 | **比法律嚴**——擋你不代表你違法 |
| **YouTube Content ID** | 指紋比對 | 事後，上傳之後 | **比法律鬆**——沒抓到不代表你合法 |
| **著作權法** | 法院 | 有人告才判 | 真正的標準 |

所以「Suno 擋我」和「有人做出來放上 YouTube」完全可以同時成立，不矛盾。

還有三件事：

1. **Content ID 最常見的結果不是下架，是「認領」。** 影片留著、廣告照跑，
   但**收益歸版權方**，上傳者一毛拿不到。而且認領對觀眾是隱形的——
   從外面看，「被認領的影片」和「安全的影片」長得一模一樣。
   那支 22 萬觀看的影片很可能只是前者

2. **那支還是搬運的**（YilanToniOoki 搬 B 站 Agroce），連原作者都不是。
   搬運帳號被砍就重開一個；**這個頻道連著 Google Classroom 和學生的課程**，
   一次版權警告的代價不是同一個量級。這是風險不對稱，不是規則不同

3. **Agroce 確實用 Suno 做出來了**，代表他有辦法過那關——而他不公開提示詞也不接教學。
   本文件這條導引音軌路線，很可能就是他在做的同一件事

### 具體怎麼收著用

- ✅ Suno 帳號是 **Pro**，可以設 private。**每一首都確認 private 有開**，
  免費版的歌會進探索頁，那就跟「只有自己聽」自相矛盾了
- ✅ 原曲、分離出來的人聲軌、guide.wav、成品，**都不進 git**（`.gitignore` 已釘死）
- ⚠️ 著作權法第 51 條寫的是「**個人或家庭**」，**不含朋友、同事、學生**。
  放給別人聽就超出範圍了
- 🔴 **絕不上傳教學頻道**。一次版權警告可能影響整個頻道，連帶影響學生的課程

> 這些是操作建議，不是法律意見。真要公開發表請找專業意見。

---

## 九之二、2026-09-12 實測記錄（成功與失敗都在這）

一整天把《至少還有你》《白色風車》都跑過。**失敗的那些比成功的更值錢。**

### 🔑 最重要的發現：Suno 有三道閘門，而且涵蓋範圍各不相同

| 閘門 | 擋什麼 | 涵蓋範圍 |
|---|---|---|
| **母帶指紋** | 既存錄音 | 商業母帶**與 Suno 自己生成過的曲子**都在內 |
| **CSI 旋律比對** | 相對音程走向 | **只有嚴管曲目**。周杰倫中；林憶蓮《至少還有你》不中 |
| **歌詞比對** | 歌詞文字 | 涵蓋很廣。《白色風車》《至少還有你》都中 |

這解釋了一整天看似矛盾的實測結果：

- ✅ 《至少還有你》的合成導引音軌**上傳成功、Cover 成功、成品好聽且旋律認得出來**
  （成品量測 3:06、123 BPM、E♭ 大調，與原曲完全一致）
- ❌ 《白色風車》的合成導引音軌**被擋**，連純單音正弦波都擋

**同樣是合成音軌，結果相反——差別在曲目，不在做法。**
所以「Suno 能不能玩改編」這個問題**沒有單一答案，要一首一首試**。
周杰倫（杰威爾）這類全網死鎖的曲目，Suno 雲端這條路整個不通，只能走本地。

> 🕳️ 這個分野差點被誤判成「Suno 一律比對旋律，整條路線死了」。
> 教訓：**測到「擋」的時候，先問「是這首擋，還是全部都擋」。** 只測一首就下全稱結論，
> 會把一條其實可行的路判死。

### ❌ 其他確認不可行的

| 做法 | 結果 |
|---|---|
| 貼原詞（《至少還有你》《白色風車》都試過） | 擋。不是只有杰威爾嚴，滾石一樣擋 |
| 上傳商業母帶 | 擋（預期內） |
| **上傳別人的 AI 成品**（Agroce 的搖滾版） | **擋** → Suno 連自己生成過的曲子都建了指紋 |
| 上傳 `.mid` 檔 | 不支援。只吃 MP3/WAV/OGG/M4A/FLAC，MIDI 要先自己渲染 |

> 🕳️ 測 `.mid` 那次畫面上出現「matches an existing recording」，其實是**前一次上傳
> 殘留的紅色橫幅**。**那個橫幅不會自己消失，測下一個之前先關掉**，
> 否則會把格式問題誤讀成版權問題。

### 🔴 疊軌打架的真正原因（不是疊軌本身不行）

疊軌成品出現「人聲跟伴奏沖到」時，**根因幾乎都是伴奏的和弦跟原曲不一樣**：

- 純文字 prompt 驅動的擴散模型（ACE-Step 只給 BPM／key 文字條件）會**自己編和弦**，
  完全脫離原曲的進行 → 主唱唱原曲、吉他彈自己的 → 走音
- **正解是讓伴奏的和聲有來源可依**，兩條都驗證過有效：
  1. **從原曲 stem 取和弦**：Demucs 4-stem 分出 `other`（鋼琴／弦樂的真實和弦），
     過破音染色成電吉他音牆 → **和弦 100% 貼合，徹底根絕走音**
  2. **ACE-Step 的 cover 模式**：用 `task_type="cover"` ＋ `audio_cover_strength`
     以原曲為骨架，時間軸可達**毫秒級對齊**

⚠️ 第二點推翻了 9/12 中午的一個誤判。當時 grep **HeartMuLa** 的碼看到
`ref_audio → muq_embed`（風格嵌入），就推論「ACE-Step 同架構、無法保留旋律」——
**那是拿 A 產品的實作去斷定 B 產品**。ACE-Step 1.5 有獨立的 cover 路徑，做得到。

### 🎤 唱腔違和要用 RVC 解，而且模型要選對

抒情原唱貼在搖滾伴奏上會能量脫節（人聲過軟、伴奏過硬）。
這個用 **RVC 歌聲轉換**處理有效，但有兩個硬條件：

- **必須用華語原生訓練的聲學模型**。外語模型（如 IU）音素空間缺中文聲母
  （zh/ch/sh/b/p…），唱中文會嚴重含糊嘟囔
- `cover_strength` 太低（0.55）模型會被文字聲調拉走而自行發明旋律；
  提到 **0.73~0.80** 才會咬合原曲音高走向

### 所以最終路線分兩條，依曲目決定

```
曲目沒被 CSI 鎖（如《至少還有你》）
  → 原曲 → Demucs → Basic Pitch → 導引音軌 → Suno Cover ＋ 自己填的詞

曲目被 CSI 鎖（如周杰倫全部）
  → 原曲 → Demucs 4-stem → other 取和弦做電吉他音牆 ＋ 重構鼓組
         → 疊原唱（可掛 RVC 換音色）→ 母帶後製
```

**兩條路原詞都只有第二條拿得到**（本地沒有歌詞過濾）。Suno 那條詞必須是自己的。

---

## 十、常見狀況

**Suno 說上傳的音檔有版權問題** → guide.wav 不該被抓到。檢查是不是不小心傳成原曲或
Demucs 分出來的 `vocals.wav`（那個仍然是商業母帶的一部分，會被抓）。

**Cover 出來旋律不像原曲** → 多半是 guide.wav 音符太亂。先自己聽一遍 guide.wav，
如果連你都聽不出是哪首歌，Suno 也認不出來。試試 `--keep-polyphonic` 關掉、
`--min-note-ms` 調大一點濾掉雜音，或改走路線 A 找現成 MIDI。

**速度整個歪掉** → `--bpm` 給錯了。回去用 analyze.py 重量一次。

**Basic Pitch 裝不起來** → Python 版本沒釘。指令要有 `--python 3.10`。

**抽出來的旋律每個音尾巴都多一個高八度的小聲音** → 泛音被誤判了。
`extract_melody.py` 預設會濾掉，如果是你自己另外抽的 MIDI 才會遇到。
順帶一提，`make_guide.py` 的合成刻意把泛音壓得很低、而且讓泛音衰減得比基音快，
就是為了不製造這種假音——改那組參數前先想一下這件事（2026-09-12 實測踩過）。

**Demucs 下載太久／硬碟不夠** → 改走路線 A 找現成 MIDI，完全不需要 Demucs。
