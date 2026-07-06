# ComfyUI MV_04 高解析九宮格工作流

## 目的

用 ComfyUI 或 RunComfy 取代一般內建生圖工具，讓 MV_04 九宮格分鏡可以穩定取得可裁切的高解析輸出。

## 家裡筆電工作流註記

本節是針對家裡筆電的本機生圖建議，不一定適用於學校電腦或其他主機。

家裡筆電目前確認條件：

- 主機：ASUS TUF Gaming A15
- 顯卡：NVIDIA GeForce RTX 4060 Laptop GPU
- VRAM：8 GB
- RAM：約 32 GB
- ComfyUI 桌面版：`C:\Users\user\AppData\Local\Programs\ComfyUI\ComfyUI.exe`
- ComfyUI 工作資料夾：`C:\Users\user\Documents\ComfyUI`
- 已確認 ComfyUI 設定選用 NVIDIA，且曾成功生圖

家裡筆電建議採用「先構圖、再放大」流程：

1. 先用 `SDXL Lightning` 或 `SDXL Base` 產生低到中解析九宮格草圖。
2. 初始九宮格建議使用 `1024 x 1024` 或 `1254 x 1254`，不要一開始直接生成 `5016 x 5016`。
3. 確認主角、服裝、場景、九格構圖都一致後，再用 Tiled Upscale、Ultimate SD Upscale 或其他放大流程處理。
4. 最終目標才放大到 `5016 x 5016`。
5. 再交給 MV_05 切成 9 張 `1672 x 1672` 分鏡圖。

不建議在家裡筆電直接一次生成 `5016 x 5016`，因為 8 GB VRAM 容易造成等待時間過長、爆顯存或輸出失敗。

目標規格：

- 整張九宮格：`5016 x 5016 px`
- 格線：`3 x 3`
- 每格：`1672 x 1672 px`
- 格式：PNG

## 推薦流程

1. 使用 FLUX 或 SDXL 生成正方形九宮格草圖；家裡筆電優先使用 SDXL Lightning 或 SDXL Base。
2. 使用參考圖或角色描述維持主角一致性。
3. 家裡筆電先輸出 `1024 x 1024` 或 `1254 x 1254` 草圖，確認構圖後再放大。
4. 使用 HiRes Fix、Tiled Diffusion 或 Ultimate SD Upscale 將整張九宮格放大到 `5016 x 5016`。
5. 輸出 `mv04-grid_5016.png`。
6. 用 MV_05 裁切成 9 張 `1672 x 1672` 分鏡 PNG。

## ComfyUI 節點建議

基礎生成：

- Checkpoint Loader：FLUX 或 SDXL 模型
- CLIP Text Encode：正向提示詞
- CLIP Text Encode：負向提示詞
- Empty Latent Image：正方形基礎尺寸，例如 `1024 x 1024` 或模型建議尺寸
- KSampler
- VAE Decode

高解析提質：

- Upscale Image / ImageScale
- Ultimate SD Upscale 或 Tiled Diffusion
- Tiled VAE Decode
- Save Image

若要角色一致性：

- IPAdapter 或 Reference Only
- ControlNet / Tile ControlNet
- 固定 seed

家裡筆電模型建議：

- 快速草圖：`sdxl_lightning_4step.safetensors`
- 穩定品質：`sd_xl_base_1.0.safetensors`
- 較吃資源的模型先保留測試，不作為 MV_04 預設流程

## MV_04 提示詞必備片段

```text
high resolution 5016 x 5016 px square image, 3x3 storyboard grid, each panel 1672 x 1672 px, cinematic MV storyboard, clean grid separation, same character in all panels, same costume in all panels, same environment in all panels, ultra detailed, PNG output, no watermark
```

## 檔案輸出建議

```text
outputs/MV_04_<專案名稱>_ComfyUI/
  mv04-grid_5016.png
  metadata.json

outputs/MV_05_<專案名稱>_九宮格提質拆圖/
  scenes-from-4x/
    scene-01-row1-col1.png
    ...
    scene-09-row3-col3.png
```

## 判斷是否成功

成功條件：

- `mv04-grid_5016.png` 實際尺寸為 `5016 x 5016`
- 九宮格邊界清楚，可等分為 3 x 3
- 每格裁切後為 `1672 x 1672`
- 主角、服裝、場景在九格中保持一致

若輸出不是 `5016 x 5016`：

- 不要直接裁低解析小格。
- 先進 MV_05 的「先整張九宮格提質，再裁切」流程。
