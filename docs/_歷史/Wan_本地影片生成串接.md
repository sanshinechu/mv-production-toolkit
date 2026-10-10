# Wan 本地影片生成串接

## 目的

把 MV 製作流程中的：

- MV_05 拆出的 9 張分鏡圖
- MV_06 產生的 9 段影片提示詞

串接到家裡筆電的 Wan 2.1 本地影片生成服務。

## 本地服務位置

本地端影片生成服務位於：

`D:\software\codex\03_本地端影片生成`

啟動檔：

`D:\software\codex\03_本地端影片生成\START_Wan_中文介面.bat`

啟動後會開啟：

- Wan 中文介面：`http://127.0.0.1:7860`
- ComfyUI 後端：`http://127.0.0.1:8188`

## 支援模式

- 文字轉影片：Wan 2.1 T2V 1.3B
- 圖片轉影片：Wan 2.1 I2V 14B 480P GGUF Q3_K_S

本 MV 流程優先使用「圖片轉影片」，因為 MV_05 已經有 9 張分鏡圖。

## 串接腳本

腳本位置：

`<雲端硬碟根目錄>\claude and codex\MV製作\scripts\wan_local_i2v_bridge.py`

預設會讀取：

- 圖片資料夾：`outputs\MV_05_快樂學習_九宮格提質拆圖_2026-05-20\scenes-from-4x`
- 提示詞檔：`outputs\MV_06_快樂學習_影片提示詞_2026-05-20.md`

## 使用方式

### 1. 先啟動本地影片服務

雙擊：

`D:\software\codex\03_本地端影片生成\START_Wan_中文介面.bat`

等瀏覽器開啟 `http://127.0.0.1:7860`，並確認狀態正常。

### 2. 先做 dry-run 檢查

dry-run 只會建立任務清單，不會真的生成影片：

```powershell
python scripts\wan_local_i2v_bridge.py --scene all
```

### 3. 測試生成第 1 段

建議先測試 1 段，不要一開始跑 9 段：

```powershell
python scripts\wan_local_i2v_bridge.py --scene 1 --submit --wait
```

預設使用低顯存測試設定：

- 秒數：3 秒
- FPS：8
- 步數：12
- 比例：1:1
- 解析度：低顯存測試

### 4. 批次送出 9 段

確認第 1 段正常後，再送出全部：

```powershell
python scripts\wan_local_i2v_bridge.py --scene all --submit
```

若要一段一段等完成：

```powershell
python scripts\wan_local_i2v_bridge.py --scene all --submit --wait
```

## 任務紀錄

腳本會建立任務紀錄：

`outputs\MV_06_快樂學習_Wan本地影片任務_2026-05-20.json`

裡面會記錄：

- 每一段使用的分鏡圖
- 送出的提示詞
- Wan local UI 回傳的 prompt ID
- 等待完成時的結果

## 注意事項

- Wan 2.1 I2V 14B 即使是低顯存版也會慢，RTX 4060 8 GB 建議先跑第 1 段測試。
- 本地 Wan 模型不會產生音訊，後續仍需另外配 SUNO 音樂。
- 若 `http://127.0.0.1:7860` 無法連線，代表 Wan 中文介面尚未啟動。
- 若 `http://127.0.0.1:8188` 無法連線，代表 ComfyUI 後端尚未啟動。
