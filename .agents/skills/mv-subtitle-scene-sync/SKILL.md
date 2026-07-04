---
name: MV 場景與字幕精準同步調整
description: 根據歌詞節奏與音樂長度，精準計算 FFmpeg 變速參數與 SRT 時間碼，實現場景切換、字幕顯示與音樂的完美同步。
triggers: 調整字幕、場景同步、MV 剪輯、歌詞對齊、FFmpeg 組裝、字幕時間軸
version: 1.0.0
---

## 🎯 核心目標
將多段固定長度（通常 8 秒）的 AI 生成影片片段，透過變速（`setpts`）與裁剪（`trim`）精確拉伸/壓縮至目標時間點，並同步更新 SRT 字幕時間碼，確保「畫面切換點」、「字幕出現點」與「歌詞/音樂節奏」三者完全吻合。

## 📐 標準工作流程

### Step 1：確認時間軸與切換點
根據歌詞段落與音樂情緒，列出每個場景的**精確切換時間**（單位：秒）。
範例結構（總長 72s）：
- Scene 1: 00:00 - 00:11 (11s)
- Scene 2: 00:11 - 00:22 (11s)
- Scene 3: 00:22 - 00:28 (6s)
- Scene 4: 00:28 - 00:44 (16s)
- Scene 5: 00:44 - 00:58 (14s)
- Scene 6: 00:58 - 01:12 (14s)
⚠️ **守則**：`SUM(場景長度) 必須嚴格等於 音樂總長度`。

### Step 2：計算 FFmpeg 變速參數
原始片段通常為固定長度（如 8 秒）。計算每個片段的變速倍率：
`變速倍率 = 目標場景長度 / 原始片段長度`
範例計算（原始 8s）：
- 11s → `1.375`
- 6s  → `0.75`
- 16s → `2.0`
- 14s → `1.75`

### Step 3：生成 FFmpeg Filter Complex
使用 `setpts` 變速、`trim` 裁剪、`setpts=PTS-STARTPTS` 重置時間戳，最後 `concat` 串接。
**固定模板結構**：
```text
[0:v]setpts=PTS*{倍率1},trim=0:{目標秒數1},setpts=PTS-STARTPTS[v1];
[1:v]setpts=PTS*{倍率2},trim=0:{目標秒數2},setpts=PTS-STARTPTS[v2];
...
[v1][v2]...concat=n={片段數}:v=1:a=0[outv];
[outv]subtitles={srt檔名}:force_style='Fontsize=28,FontName=Microsoft JhengHei,PrimaryColor=&HFFFFFF&,OutlineColor=&H000000&,Outline=2,Shadow=1,Alignment=2,MarginV=40'[final]
```

### Step 4：同步更新 SRT 字幕檔
根據 Step 1 的時間軸撰寫 SRT。核心原則：
1. **單句顯示**：一句歌詞一個區塊，避免斷句過碎。
2. **時間對齊**：字幕起始時間碼應 **等於或略晚於** 場景切換時間（建議延後 0.5~1 秒，符合視覺認知）。
3. **格式嚴格**：`HH:MM:SS,mmm --> HH:MM:SS,mmm`

### Step 5：執行組裝與驗證
執行 FFmpeg 指令後，檢查清單：
- [ ] 總長度是否等於音樂長度？
- [ ] 場景切換點是否與 SRT 時間碼一致？
- [ ] 字幕是否為完整單句？有無錯字？
- [ ] 音畫是否同步？無黑屏或跳幀？

## ⚠️ 關鍵注意事項與踩坑紀錄

### 1. FFmpeg `setpts` 與 `trim` 的順序
**必須先 `setpts` 變速，再 `trim` 裁剪，最後 `setpts=PTS-STARTPTS` 重置**。
錯誤寫法會導致黑畫面或時間戳錯亂。
✅ 正確範例：`setpts=PTS*1.375,trim=0:11,setpts=PTS-STARTPTS`

### 2. 字幕與場景的「微秒級」同步
- 若字幕比場景早出現：觀眾會先看到字，後看到畫面，產生割裂感。
- **修正原則**：當用戶要求「X 秒出現字幕」時，直接修改 SRT 該段落起始時間為 `00:00:X,000`，並同步調整前後段落的結束時間，保持總長度不變。

### 3. 總長度守恆定律
調整任何一個場景的長度時，必須同步增減**相鄰場景**的長度。
例：若 Scene 3 需從 6s 改為 8s，則 Scene 4 必須從 16s 縮為 14s，確保總和仍為 72s。

## 🛠️ 快速指令模板（PowerShell）

```powershell
$out = "outputs\final\{專案名}_MV_最終版.mp4"
ffmpeg -y -i 01.mp4 -i 02.mp4 -i 03.mp4 -i 04.mp4 -i 05.mp4 -i 06.mp4 -i music.mp3 `
-filter_complex "[0:v]setpts=PTS*1.375,trim=0:11,setpts=PTS-STARTPTS[v1]; [1:v]setpts=PTS*1.375,trim=0:11,setpts=PTS-STARTPTS[v2]; [2:v]setpts=PTS*0.75,trim=0:6,setpts=PTS-STARTPTS[v3]; [3:v]setpts=PTS*2.0,trim=0:16,setpts=PTS-STARTPTS[v4]; [4:v]setpts=PTS*1.75,trim=0:14,setpts=PTS-STARTPTS[v5]; [5:v]setpts=PTS*1.75,trim=0:14,setpts=PTS-STARTPTS[v6]; [v1][v2][v3][v4][v5][v6]concat=n=6:v=1:a=0[outv]; [outv]subtitles=lyrics_final.srt:force_style='Fontsize=28,FontName=Microsoft JhengHei,PrimaryColor=&HFFFFFF&,OutlineColor=&H000000&,Outline=2,Shadow=1,Alignment=2,MarginV=40'[final]" `
-map "[final]" -map 6:a -c:v libx264 -c:a aac -b:a 192k -pix_fmt yuv420p $out
```

## 🔄 迭代優化心法
1. **先定骨架**：先確認切換時間點，算出變速倍率。
2. **再填血肉**：根據切換點撰寫 SRT，確保字幕起始時間 >= 場景切換時間。
3. **微調節奏**：根據用戶反饋，只修改 SRT 時間碼與對應 FFmpeg `trim` 秒數，重新計算相鄰場景長度以維持總長不變。
4. **一鍵重跑**：保留 Filter Complex 模板，只需替換數字即可快速生成新版本（v1, v2...）。
