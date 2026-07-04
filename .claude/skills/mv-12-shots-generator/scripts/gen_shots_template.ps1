# gen_shots_template.ps1 — 分鏡批次生圖範本
# 使用方式：複製到專案 tools/，填入 $Base 與 $Cuts，執行即可
# 生圖順序：draw_cf（Cloudflare，預設）→ 失敗時 draw-free（Pollinations，備援）
# 注意：本檔必須存成 UTF-8 with BOM（PowerShell 5.1 讀無 BOM 中文會炸）

$ErrorActionPreference = "Continue"

# === 依專案調整這三行 ===
$DrawCf   = Join-Path $PSScriptRoot "draw_cf.ps1"                                      # draw_cf 腳本位置
$DrawFree = "$env:USERPROFILE\.config\opencode\skills\draw-free\draw-free.ps1"        # draw-free 備援
$ShotsDir = Join-Path (Split-Path -Parent $PSScriptRoot) "mv_project\shots"           # 輸出目錄

# === 統一風格基底（跨張一致性的關鍵；免費模型勿用寫實風格）===
$Base = "full page children's crayon drawing filling the entire frame, white sketchbook paper background, drawn by a 7-year-old kid, naive doodle style, wobbly imperfect lines, colorful wax crayon texture, simple stick figures with round faces, no photorealism, no text"

# === cuts 清單：Name 需與組裝腳本 STORYBOARD 前綴對齊 ===
$Cuts = @(
    @{ Name = "cut01_example_scene"; Prompt = "scene description here" }
    # @{ Name = "cut02_...";         Prompt = "..." }
)

$Done = 0
$Failed = @()
foreach ($c in $Cuts) {
    # 已有同前綴圖片就跳過（重生個別 cut：刪掉該前綴的圖再重跑）
    $existing = Get-ChildItem -Path $ShotsDir -Filter "$($c.Name)_*.png" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "[SKIP] $($c.Name) 已存在" -ForegroundColor DarkGray
        $Done++
        continue
    }

    Write-Host "`n=== $($c.Name) ===" -ForegroundColor Cyan

    # 1. 預設走 draw_cf（Cloudflare Workers AI）
    & powershell -ExecutionPolicy Bypass -File $DrawCf "$($c.Prompt), $Base" `
        -Name $c.Name -OutDir $ShotsDir -Steps 8

    # 2. 失敗才落到 draw-free（Pollinations，可出 16:9）
    $check = Get-ChildItem -Path $ShotsDir -Filter "$($c.Name)_*.png" -ErrorAction SilentlyContinue
    if (-not $check) {
        Write-Host "[備援] draw_cf 失敗，改用 draw-free（Pollinations）..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $DrawFree "$($c.Prompt), $Base" `
            -Size 1920x1080 -Name $c.Name -OutDir $ShotsDir
        $check = Get-ChildItem -Path $ShotsDir -Filter "$($c.Name)_*.png" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }

    if ($check) { $Done++ } else { $Failed += $c.Name }
}

Write-Host "`n=== 完成 $Done/$($Cuts.Count) ===" -ForegroundColor Green
if ($Failed.Count -gt 0) {
    Write-Host "失敗清單：$($Failed -join ', ')" -ForegroundColor Red
    exit 1
}
