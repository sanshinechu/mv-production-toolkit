# draw_cf.ps1 — Cloudflare Workers AI 免費生圖（FLUX.1 schnell）
# 憑證來源（擇一）：
#   1. 環境變數 CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_API_TOKEN
#   2. 金鑰檔 %USERPROFILE%\.cloudflare_ai（兩行：ACCOUNT_ID=xxx 與 API_TOKEN=xxx）
# 用法：
#   powershell -ExecutionPolicy Bypass -File draw_cf.ps1 "a cat reading a book"
#   powershell -ExecutionPolicy Bypass -File draw_cf.ps1 "school playground sunset" -Name cut01 -OutDir shots -N 2 -Steps 6

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$Prompt,

    [int]$Steps = 6,          # 1-8，越高細節越多
    [int]$Seed = -1,
    [int]$N = 1,
    [string]$Name = "image",
    [string]$OutDir = ".\generated"
)

$ErrorActionPreference = "Stop"

# === 讀憑證 ===
$AccountId = $env:CLOUDFLARE_ACCOUNT_ID
$ApiToken  = $env:CLOUDFLARE_API_TOKEN
$KeyFile = Join-Path $env:USERPROFILE ".cloudflare_ai"
if ((-not $AccountId -or -not $ApiToken) -and (Test-Path $KeyFile)) {
    foreach ($line in Get-Content $KeyFile) {
        if ($line -match "^ACCOUNT_ID=(.+)$") { $AccountId = $Matches[1].Trim() }
        if ($line -match "^API_TOKEN=(.+)$")  { $ApiToken  = $Matches[1].Trim() }
    }
}
if (-not $AccountId -or -not $ApiToken) {
    Write-Host "[ERR] 找不到憑證。請設環境變數 CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN" -ForegroundColor Red
    Write-Host "      或建立 $KeyFile（內容兩行：ACCOUNT_ID=xxx 與 API_TOKEN=xxx）" -ForegroundColor Red
    exit 1
}

$PromptText = ($Prompt -join " ").Trim()
$Url = "https://api.cloudflare.com/client/v4/accounts/$AccountId/ai/run/@cf/black-forest-labs/flux-1-schnell"

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "Cloudflare Workers AI 生圖中（flux-1-schnell, steps=$Steps, n=$N）-> $OutDir" -ForegroundColor Cyan

$SavedFiles = @()
for ($i = 1; $i -le $N; $i++) {
    if ($Seed -ge 0) { $CurrentSeed = $Seed + ($i - 1) }
    else             { $CurrentSeed = Get-Random -Minimum 1 -Maximum 999999999 }

    $Body = @{ prompt = $PromptText; steps = $Steps; seed = $CurrentSeed } | ConvertTo-Json

    $Suffix = if ($N -gt 1) { "_$i" } else { "" }
    $FilePath = Join-Path $OutDir "${Name}_${Stamp}${Suffix}.png"

    Write-Host "  [$i/$N] 生成中... seed=$CurrentSeed" -ForegroundColor Yellow
    try {
        $Resp = Invoke-RestMethod -Uri $Url -Method Post -Body $Body -ContentType "application/json" `
            -Headers @{ Authorization = "Bearer $ApiToken" } -TimeoutSec 120
        if (-not $Resp.success) {
            Write-Host "  [FAIL] API 回傳失敗：$($Resp.errors | ConvertTo-Json -Compress)" -ForegroundColor Red
            continue
        }
        [System.IO.File]::WriteAllBytes($FilePath, [Convert]::FromBase64String($Resp.result.image))
        $SizeKB = [math]::Round((Get-Item $FilePath).Length / 1024.0, 1)
        Write-Host "  [OK] $FilePath (${SizeKB} KB)" -ForegroundColor Green
        $SavedFiles += $FilePath
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($SavedFiles.Count -gt 0) {
    Write-Host "`n完成！共 $($SavedFiles.Count) 張：" -ForegroundColor Green
    $SavedFiles | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "`n失敗：沒有圖片成功生成" -ForegroundColor Red
    exit 1
}
