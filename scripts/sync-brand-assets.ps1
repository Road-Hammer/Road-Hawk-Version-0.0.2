# Sync STWL brand assets from canonical D: vault into the web app.
$repo = Split-Path $PSScriptRoot -Parent
$dest = Join-Path $repo "web\public\brand"
$sourceLogo = "D:\STWL\STWL\SCREENSHOTS\STWL SQUARE PIC.png"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

if (-not (Test-Path $sourceLogo)) {
    Write-Error "STWL logo not found at: $sourceLogo"
    exit 1
}

Copy-Item $sourceLogo (Join-Path $dest "stwl-logo.png") -Force
Write-Host "Synced STWL logo from D:\STWL to web/public/brand/stwl-logo.png"