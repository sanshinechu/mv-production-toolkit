---
title: 參考曲分析：至少還有你（Suno 搖滾現場版）
date: 2026-09-11
machine: 家裡用筆電
tags:
  - MV製作
  - Suno
  - 編曲分析
  - 參考曲
---

# 參考曲分析：至少還有你（Suno 搖滾現場版）

老師很喜歡這首的編排，想知道它是怎麼做出來的，之後拿來套自己的 Suno 作品。
對應 12 步流程的 **Step 1（歌詞創作與曲風風格）**。

## 一、來歷

| 項目 | 內容 |
|---|---|
| 聽到的版本 | YouTube [LMTUJ0PrkKQ](https://www.youtube.com/watch?v=LMTUJ0PrkKQ)（頻道 YilanToniOoki，**B 站搬運**），5 分 18 秒，約 22 萬次觀看 |
| 原作者 | B 站 UP 主 **Agroce**：[BV1gBgs6SEHd](https://www.bilibili.com/video/BV1gBgs6SEHd/)，2026-08-13 發布，播放 1,077 萬 |
| 原曲 | 林憶蓮《至少還有你》（2000，林夕詞、Davy Chan 曲、劉志遠編） |
| 製作工具 | 作者自述**用 Suno 改編**，標題寫「Hi-Res 音質」；**沒公開提示詞，也不接教學** |

**觀察：**

- 作者是**系列量產**：「搖滾現場」系列還有《布拉格廣場》《日不落》《左邊》《妥協》；
  同一首《至少還有你》另外做了一版「搖滾流行」（[BV1wogs6qEwt](https://www.bilibili.com/video/BV1wogs6qEwt/)）
  → 有固定配方，而且同一首會生多種風格再挑
- **畫面只有一張 AI 生成圖**：東亞女主唱抱紅色電吉他、紅藍舞台燈、大字標題，
  下方一行歌詞字幕，左上浮水印，從頭到尾沒有動態影片。**流量全靠聲音撐**
  → 如果目標是音樂本身，Step 7～9（生影片、打光）可以大幅簡化
- 旋律聽得出原曲，推測是走 Suno 的 **Cover／上傳音訊改編**，不是只貼歌詞（只貼歌詞 Suno 會寫新旋律）。**這點是推測，作者沒說**

## 二、分析方法

聲音是 AI 聽不到的，所以改用程式量測＋頻譜圖「用看的」判讀：

- `分析腳本/analyze.py`：速度、調性（每 15 秒）、每秒音量／鼓／低音比例、自動段落切分
- `分析腳本/spec.py`：畫頻譜圖（`頻譜圖/` 裡那 6 張）
- `分析腳本/vocal.py`：粗略拆出主旋律線，看各段突出程度與音域

時間點有數據撐腰；**樂器名稱是判讀，可能有少數誤差**。主旋律拆分用的是簡易方法（REPET-SIM），吉他旋律也會混進來，只看趨勢。

> 音檔**沒有**存進專案（有版權），只在當次暫存區，對話結束即清除。要重跑就重新下載。

## 三、基本數據

- **速度**：全曲穩定 **123 BPM**，沒有加速或放慢 → 張力靠編排堆，不靠速度
- **調性**：全曲 **E♭ 大調**，**最後副歌沒有升 Key**（4:45 附近測到 B♭ 是屬和弦，最後副歌前的正常現象）
- 樂譜網站多標原曲為 E 調 → 這版低半音。搖滾樂團常整把吉他調低半音（聲音較厚、主唱較好唱），
  可能是 Suno 學到的習慣，也可能是巧合

## 四、整首歌的「劇本」

| 時間 | 發生什麼事 | 數據證據 |
|---|---|---|
| 0:00–0:02 | **觀眾歡呼**開場 | 頻譜 1 kHz 附近一團霧狀雜訊＝人群聲 |
| 0:02–0:17 | 前奏：沒有鼓，低音只拉長音，一條帶顫音的吉他旋律慢慢鋪 | 低音比例 0.6～2% |
| **0:17–0:19** | **又一聲歡呼＋全團進場** | 低音比例 2% → 10% |
| 0:32–1:02 | 主歌收著唱：音量退、鼓變稀，人聲在低音區 | -21 dB；人聲在 250～400 Hz |
| 1:02–3:58 | **爬樓梯**：每一輪都比前一輪滿一點，近 3 分鐘沒往下掉 | -19 → -17 → -16 → -15 dB |
| 3:15–3:30 | 主旋律唱到全曲最高音（約 C6） | |
| **3:58–4:02** | **全團急停**，只剩人聲和歡呼 | 高頻整片變暗 |
| **4:08–4:20** | **樂團齊奏重拍**，一格一格地打 | 打擊比例 0.46～0.55（全曲最高），低音出現規律空格 |
| **4:21** | 全團回歸，**最高潮的副歌** | 主旋律占比全曲最高 |
| **4:44–4:54** | **突然抽空**，幾乎只剩人聲 | -23 dB，高頻全暗 |
| 4:55–5:10 | 最後一次全開 | |
| 5:10–5:18 | 長音收尾＋**觀眾歡呼淡出** | 結尾又出現人群聲 |

對照圖：`頻譜圖/4_急停與齊奏_0356-0436.png`、`頻譜圖/5_抽空與結尾_0436-0518.png` 最能看出高潮前那兩次「收」。

## 五、好聽的三個關鍵

1. **歡呼只放在頭、中、尾三個點**，其他時候乾淨 → 一直有「現場感」，但不吵到人聲
2. **慢慢爬、不急著爆**。多數 AI 翻唱第一次副歌就開到最大，後面沒地方推；這首一層層加，4 分鐘還有力氣
3. **高潮前先「收」兩次**（4:00 急停、4:45 抽空）→ 像跳遠前蹲低，安靜那一下讓後面加倍大聲

## 六、Suno 範本：搖滾現場版

**風格描述**（依分析結果自寫）：

> Live rock concert recording of a Mandopop ballad, 123 BPM, female lead vocal starting restrained in a low register and building to powerful belted high notes, arena reverb, crowd cheering at the start and end, overdriven electric guitars with melodic lead lines, driving live drums, warm bass, gradual build-up across the song, dramatic band stop before the final chorus, stripped-down quiet breakdown then full-band explosive last chorus, big sustained ending with applause.

**歌詞框結構標籤**（關鍵：只靠風格描述，Suno 不會自己安排急停和抽空）：

```
[Intro, crowd cheering, clean guitar, no drums]
[Band Kicks In]
[Verse, restrained, sparse drums]
[Chorus, full band]
...（中間照歌詞走，每輪副歌可加 building / bigger）
[Break, band stops, vocals and crowd only]
[Drum Break, band hits in unison]
[Chorus, climax, powerful vocals]
[Breakdown, quiet, vocals only]
[Final Chorus, explosive, full band]
[Outro, sustained chord, crowd applause, fade out]
```

## 七、延伸：周杰倫《白色風車》能不能做成這種版本？

> 🔴 **2026-09-11 實測：Suno 認出版權歌詞，直接擋下。** 不走繞過的路，
> 改做原創新歌《陪你淋雨》＋自己的畢業歌搖滾現場版，見 [套用範例.md](套用範例.md)。
> 以下是當時的評估，留作參考。

**做得出來，但要注意兩件事。**

### 版權

- **只放在自己的 Suno 私下聽**：風險低。記得把歌設成**私人（Private）**，
  不要公開到 Suno 的探索頁或分享連結出去
- **公開上傳 YouTube**：Content ID 幾乎一定抓到，杰威爾管得嚴 → 輕則被認領、重則下架＋警告
- 🔴 **絕不能傳到教學頻道**（連著 Google Classroom），一次版權警告就可能影響整個頻道

### 技術：旋律要「像」比想像中難

| 做法 | 結果 |
|---|---|
| 只貼歌詞＋風格描述 | Suno 寫**新旋律**，歌詞對但聽起來不是《白色風車》 |
| 上傳原曲讓 Suno 改編 | Suno 會偵測商業錄音，**原唱多半被擋** |
| 自己彈／哼一段旋律上傳再改編 | 最有機會保留旋律；仍屬翻唱，受上面版權規則管 |

另外 Suno 對知名歌詞也可能擋，被擋就只能自己調整。

### 風格要調整

《白色風車》是溫柔浪漫的抒情歌，不像《至少還有你》副歌本身就有爆發力，硬搖滾套上去容易變吼。
改走 **power ballad**：前段鋼琴＋輕吉他，慢慢疊到後段全團爆開，
第五節的「爬樓梯」和「高潮前先收」兩招正好適用。

**風格描述**（男聲版，自寫）：

> Live arena power ballad version of a Mandopop love song, warm male lead vocal with a soft, intimate tone in the verses growing into passionate, soaring choruses, opening with gentle piano and clean electric guitar over light crowd cheering, gradual build-up with each chorus fuller than the last, melodic guitar solo in the bridge, dramatic band stop before the final chorus, quiet piano-and-vocal breakdown, then an explosive full-band last chorus, big sustained ending with crowd applause.

**結構標籤**（括號處貼自己的歌詞，本文件不收錄歌詞）：

```
[Intro, crowd cheering, soft piano, clean guitar]
[Verse 1, intimate, piano and light drums]
（第一段主歌）
[Pre-Chorus, building]
（導歌）
[Chorus, full band]
（副歌）
[Verse 2, band stays in, slightly bigger]
（第二段主歌）
[Chorus, bigger, backing vocals]
（副歌）
[Guitar Solo, melodic, emotional]
[Break, band stops, vocal and crowd only]
[Breakdown, piano and vocal, quiet]
[Final Chorus, explosive, full band]
[Outro, sustained chord, crowd applause, fade out]
```

**小技巧**：同設定**生 4～6 首**再挑（Agroce 同一首也做兩種風格）。
挑的時候**先聽 4 分鐘左右的急停**，那裡最能看出成不成功。

## 八、之後怎麼重用

拿自己的 Suno 成品跑同一套分析，跟本文件第四節對照，就知道「爬樓梯」「急停」「抽空」有沒有做出來：

```bash
uv run --with librosa python analyze.py 我的歌.mp3
uv run --with librosa --with matplotlib python spec.py 我的歌.mp3 236-276 276-318
```

看能量表：主歌到最後副歌的音量應該**逐段上升**；急停與抽空處應該看到明顯的 dB 掉落和高頻變暗。
