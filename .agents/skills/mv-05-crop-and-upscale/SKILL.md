---
name: 截取九宮格影像並放大提升品質
description: 從 MV_04 九宮格分鏡圖的同一張來源圖片中，先將整張九宮格 4x 放大提質，再從高解析九宮格實際裁切出 9 張獨立分鏡 PNG。
triggers: 截取九宮格, 放大九宮格, MV_05, 圖片放大, 提升畫質, 全部九張, 全部處理
version: 2.4.0
author: MV 製作專案
---

# MV_05 截取九宮格影像並放大提升品質

## 目標

本 Skill 用於處理 MV_04 產生的九宮格分鏡圖。

預設行為會先檢查來源解析度，再決定是否需要提升整張九宮格，不是重新生圖：

1. 找到或確認 MV_04 產生的同一張九宮格來源圖片。
2. 若來源已是 `5016 x 5016`，直接裁切成 9 張 `1672 x 1672` 分鏡。
3. 若來源低於 `5016 x 5016`，先將整張九宮格來源圖做 4x 或等比例放大提質，輸出一張高解析九宮格。
4. 再依 3x3 位置，從高解析九宮格裁切出 9 張獨立分鏡 PNG。
5. 每一張依序命名輸出，不保留九宮格邊框，不重新生成內容。
6. 只有在使用者另外要求 AI 修復、重繪或風格提質時，才使用生圖工具做後製。

## 使用規則

- 使用者若說「全部九張」、「全部一起處理」、「全部處理」、「輸出成單張的 9 張圖片」，直接啟動「整張九宮格 4x 提質後再裁切」流程。
- 不需要再詢問 Row/Column。
- 若使用者明確指定單一格，才改用單格截取流程。
- 若目前沒有可用的九宮格圖片，先請使用者上傳或指定 MV_04 九宮格圖片。
- 「直接處理」代表先把來源九宮格整張 4x 放大，再裁切輸出 9 張檔案，不代表呼叫生圖工具。
- 如果來源已由 MV_04 ComfyUI 工作流輸出為 `5016 x 5016`，不要再放大，直接裁切。
- 「放大提升品質」只在來源低於目標解析度時作用在整張九宮格來源圖上，而不是先裁小圖再放大。
- 必須保留原始九宮格來源圖；整張 4x 九宮格另存到 `upscaled-grid-4x/`，9 張裁切結果另存到 `scenes-from-4x/`。
- 只有使用者明確說「用 AI 重繪」、「AI 修復」、「重新生成高畫質版本」時，才可呼叫生圖工具；使用前要提醒這會改變原圖內容，不是純裁切。
- 本專案圖片流程規則仍然適用：圖片相關 AI 生成/重繪步驟要先提供提示詞，使用者明確同意後才生圖。

## 重要區分

### 正確：先檢查解析度，再裁切或整張提質

這是 MV_05 的主要流程。輸入一張九宮格圖片，先檢查尺寸：

- 來源內容完全來自原圖。
- 若來源是 `5016 x 5016`，直接裁切成 9 張 `1672 x 1672`。
- 若來源是 `1254 x 1254` 或其他低解析，先放大整張圖，讓每個分鏡在裁切前就有較高解析度。
- 每張單圖對應高解析九宮格的一格。
- 可做解析度放大與輕微銳化，但不能擅自改變角色、構圖或內容。

### 避免：先裁切再放大

除非使用者明確要求，避免先把低解析九宮格裁成小圖再放大，因為小格資訊量較少，容易讓畫質變差、邊緣模糊或細節破碎。

### 錯誤：重新生成九張圖或九宮格

不要把這個任務交給生圖工具重新生成，除非使用者明確要求 AI 重繪。以下都不是 MV_05 的預設行為：

- 重新生成一張包含 9 個畫面的拼貼圖。
- 生成「看起來像」原九宮格的 9 張新圖片。
- 用提示詞要求模型「輸出 9 張」，但沒有實際裁切原圖。

## 全部 9 張處理流程：檢查解析度後裁切

### 1. 確認來源

來源圖片應為 MV_04 九宮格分鏡圖，通常是 3x3 排列：

```text
[Row 1, Column 1]  [Row 1, Column 2]  [Row 1, Column 3]
[Row 2, Column 1]  [Row 2, Column 2]  [Row 2, Column 3]
[Row 3, Column 1]  [Row 3, Column 2]  [Row 3, Column 3]
```

### 2. 檢查來源解析度

- 若來源為 `5016 x 5016`：直接進入裁切。
- 若來源為 `1254 x 1254`：先建立 `5016 x 5016` 的 4x 九宮格。
- 若來源為其他尺寸：保持正方形比例，先等比例提升到可被 3 整除的高解析尺寸；正式目標仍以 `5016 x 5016` 為準。

### 3. 必要時先建立整張 4x 九宮格

先對整張來源圖做 4x 放大，保留九宮格完整結構：

- 若來源九宮格是 `1254 x 1254`，4x 九宮格應為 `5016 x 5016`。
- 4x 九宮格保存到 `upscaled-grid-4x/`。
- 檔名建議為 `mv04-grid_4x.png`。
- 使用高品質插值，例如 Bicubic、Lanczos、HighQualityBicubic。
- 可做輕微銳化與去噪，但不要重繪內容。

### 4. 從高解析九宮格裁切

若高解析九宮格是標準 3x3，裁切方式如下：

- `cellWidth = imageWidth / 3`
- `cellHeight = imageHeight / 3`
- Row 1 使用 `y = 0`
- Row 2 使用 `y = cellHeight`
- Row 3 使用 `y = cellHeight * 2`
- Column 1 使用 `x = 0`
- Column 2 使用 `x = cellWidth`
- Column 3 使用 `x = cellWidth * 2`

若九宮格有明顯外框或內距，先在原始圖階段確認外框比例，再套用到 4x 圖；必要時裁掉外框後再等分。不要猜測裁切偏移太大，避免切掉人物。

### 5. 九張獨立輸出

請從 4x 高解析九宮格拆成 9 張單獨圖片，依序命名或標示為：

1. `scene-01-row1-col1`
2. `scene-02-row1-col2`
3. `scene-03-row1-col3`
4. `scene-04-row2-col1`
5. `scene-05-row2-col2`
6. `scene-06-row2-col3`
7. `scene-07-row3-col1`
8. `scene-08-row3-col2`
9. `scene-09-row3-col3`

每張圖片都要是完整單張畫面，不保留九宮格邊框，不要把 9 張合併回一張拼圖。

建議輸出資料夾：

```text
outputs/MV_05_<專案名稱>_九宮格提質拆圖/
```

建議子資料夾：

```text
upscaled-grid-4x/   # 存整張 4x 九宮格
scenes-from-4x/     # 存從 4x 九宮格裁出的 9 張分鏡
```

若原始九宮格是 `1254 x 1254`，4x 九宮格為 `5016 x 5016`，每張分鏡應為 `1672 x 1672`。

### 5. 畫質與構圖要求

每一張輸出圖都要符合：

- 全幅獨立畫面，不含九宮格框線。
- 主體清楚，盡量保留原分鏡內容。
- 不要做構圖補全或生成新背景，除非使用者明確要求 AI 重繪。
- 光線、色調、角色外觀與原九宮格保持一致。
- 解析度與細節足以作為影片生成首幀。
- 不要加入浮水印、簽名、亂碼文字或多餘字幕。

## PowerShell 先 4x 再裁切範例

在 Windows / PowerShell 環境中，可用下列流程：先把整張九宮格放大 4x，再從高解析九宮格裁切 9 張。請把 `$src` 和 `$outRoot` 換成實際路徑：

```powershell
Add-Type -AssemblyName System.Drawing

$src = "C:\path\to\mv04-grid.png"
$outRoot = "<雲端硬碟根目錄>\claude code\MV製作\outputs\MV_05_專案名稱_九宮格提質拆圖"
$gridOut = Join-Path $outRoot "upscaled-grid-4x"
$sceneOut = Join-Path $outRoot "scenes-from-4x"
New-Item -ItemType Directory -Force -Path $gridOut | Out-Null
New-Item -ItemType Directory -Force -Path $sceneOut | Out-Null

$img = [System.Drawing.Bitmap]::FromFile($src)
$grid4x = New-Object System.Drawing.Bitmap ($img.Width * 4), ($img.Height * 4)
$g = [System.Drawing.Graphics]::FromImage($grid4x)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
$g.DrawImage($img, 0, 0, $grid4x.Width, $grid4x.Height)
$gridFile = Join-Path $gridOut "mv04-grid_4x.png"
$grid4x.Save($gridFile, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
$g.Dispose()

$cellW = [int]($grid4x.Width / 3)
$cellH = [int]($grid4x.Height / 3)

for ($r = 0; $r -lt 3; $r++) {
  for ($c = 0; $c -lt 3; $c++) {
    $idx = ($r * 3 + $c + 1)
    $rect = New-Object System.Drawing.Rectangle ($c * $cellW), ($r * $cellH), $cellW, $cellH
    $crop = $grid4x.Clone($rect, $grid4x.PixelFormat)
    $file = Join-Path $sceneOut ("scene-{0:D2}-row{1}-col{2}.png" -f $idx, ($r + 1), ($c + 1))
    $crop.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
    $crop.Dispose()
  }
}

$grid4x.Dispose()
```

## AI 後製提示詞模板

只有使用者明確要求 AI 提質、AI 修復或重新生成高畫質版本時，才使用本段。使用前要先說明：AI 後製可能改變人物細節與畫面內容。

```text
請以這張已裁切出的單張 MV 分鏡圖為基礎，只做高畫質修復與細節增強，不要改變構圖、人物姿勢、服裝、場景或鏡頭語言。

請修復臉部、手部、服裝邊緣與背景細節，提升清晰度與電影感光線，保持原圖角色一致、色調一致、場景一致。不要新增字幕、浮水印、額外文字或不相關物件。

輸出為單張高清圖片，不要拼貼，不要九宮格。
```

## 單格處理備援

如果使用者明確指定 Row/Column，才使用單格流程：

1. 確認指定格子，例如 `Row 2, Column 3`。
2. 先將整張來源九宮格 4x 放大。
3. 從 4x 九宮格實際裁切指定格。
4. 輸出單張高解析 PNG。
5. 保持角色、場景、光線與原九宮格一致。

## 下一步

完成 9 張獨立圖片後，進入：

1. **MV_06 生成影片提示詞**：為每張圖片撰寫圖生影片動態提示詞。
2. **MV_09 Google Flow 微電影製作**：若要做無縫轉場或首尾幀影片，可接續使用。
