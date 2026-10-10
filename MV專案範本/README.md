# {{MV名}}

> 由 `python scripts/new_mv.py "{{MV名}}"` 從 `MV專案範本/` 建立（{{建立日期}}）。
> 一支 MV 的所有文件與素材都放這個資料夾；`outputs/` 被 gitignore，靠 Google Drive 同步。
> 影片路線唯一依據：[影片分流策略](../../docs/影片分流策略.md)；畫面規範：[6 項基本原則](../../docs/影片製作基本原則.md)。

## 進度檢核（做完打勾，寫上日期）

| # | 步驟 | 工具 | 產出（本資料夾） | 完成 |
|---|---|---|---|---|
| 1 | 企劃 | cowrite `--flow mv`（劇情企劃） | `brief.md` | [ ] |
| 2 | 歌詞與曲風 → SUNO 生歌 | mv-01（共修）＋ SUNO | `music/` 原曲 mp3 | [ ] |
| 3 | 主角造型 | mv-02（共修） | `角色錨點.md`＋`shots/character_ref.png`（**單張半身**，不是左右分割定妝圖） | [ ] |
| 4 | 時間軸分鏡表 | mv-11 | `storyboard_v1.md`（秒數加總＝歌長、單鏡 ≤10 秒、標最難一鏡） | [ ] |
| 5 | 場景提示詞、分鏡圖 | mv-03、mv-04（共修）、mv-12 生圖 | `shots/cutNN_*.png` | [ ] |
| 6 | 影片提示詞 | mv-06（**審核**，三家無意見） | 定案稿在共修紀錄 → 記到 `共審紀錄.md` | [ ] |
| 7 | 選路線 | 老師決定整支 MV 走 🅰 Colab H3 或 🅱 Google Flow | 寫在 `brief.md` 最後一行 | [ ] |
| 8🅰 | H3 分鏡審核 → 拆檔 → 清單 → 生成 → 放大 → 搬回 | `--flow mv-h3`、`h3_specs_from_review.py`、`h3_batch.py`、`collect_videos.py` | `videos-raw/cutNN_*.mp4` | [ ] |
| 8🅱 | Flow 提示詞審核 → 老師在 Flow 生成 → 放回 | `--flow mv-flow`、`collect_videos.py --check` | `videos-raw/cutNN_*.mp4` | [ ] |
| 9 | 組裝 1080p | `make_mv.py --videos --storyboard --size 1920x1080` | `{{MV名}}_完整MV.mp4` | [ ] |
| 10 | 自動檢查 | `review_mv.py --storyboard` | `review/` | [ ] |
| 11 | ⛔ **人工抽幀**（字幕淨空／亂碼／角色／轉場） | 老師看 `review/*_pass1.jpg`、`*_cuts.jpg` | 老師說「抽幀確認 OK」→ 記日期 | [ ] |
| 12 | 打包與上傳 | mv-production-packaging、youtube-publisher | `metadata.md`、`cover.png`、`youtube-upload.json` | [ ] |

## 常用指令（在 01_MV製作 根目錄執行）

```
python scripts/collect_videos.py "{{MV名}}" --storyboard "outputs/{{MV名}}/storyboard_v1.md" [--check]
python scripts/make_mv.py --videos "outputs/{{MV名}}/videos-raw" --storyboard "outputs/{{MV名}}/storyboard_v1.md" --size 1920x1080 --music "outputs/{{MV名}}/music/<歌>.mp3" --out "outputs/{{MV名}}/{{MV名}}_完整MV.mp4"
python scripts/review_mv.py "outputs/{{MV名}}/{{MV名}}_完整MV.mp4" --music "outputs/{{MV名}}/music/<歌>.mp3" --storyboard "outputs/{{MV名}}/storyboard_v1.md"
```

## 資料夾

| 位置 | 放什麼 |
|---|---|
| `brief.md` | 主題、受眾、曲風方向、選定路線 |
| `角色錨點.md` | 角色一致性參考詞（之後每份提示詞逐字沿用） |
| `storyboard_vN.md` | mv-11 分鏡表；改版就加 N，舊版不刪 |
| `共審紀錄.md` | 各階段共修資料夾名（`--from` 要用）與定案日期 |
| `shots/` | 分鏡圖、角色參考圖（H3 首幀會複製成 `cutNN_first.png` 放進 colab_mv） |
| `music/` | SUNO 原曲（別放進 git） |
| `videos-raw/` | 兩條路線的影片成品 `cutNN_短名.mp4`，1920×1080、24 fps；舊版自動移到 `_old/` |
| `review/` | review_mv.py 的抽幀圖與數字 |
| `metadata.md` | YouTube 7 區塊 |
