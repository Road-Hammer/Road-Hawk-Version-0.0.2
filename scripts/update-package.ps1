# Pull latest Road Hawk code and refresh local Python + web dependencies.
param(
    [string]$Branch = "Road-Hawk",
    [switch]$SkipPull,
    [switch]$SkipTests,
    [switch]$IncludeOcr,
    [switch]$ProductionWeb
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

. (Join-Path $PSScriptRoot "ensure-node-path.ps1")

Write-Host "Road Hawk package update"
Write-Host "Repository: $repo"

if (-not $SkipPull) {
    Write-Host "Fetching and pulling origin/$Branch..."
    git fetch origin
    git pull origin $Branch
}

Write-Host "Syncing version metadata..."
python (Join-Path $PSScriptRoot "sync-version.py")

if (Test-Path (Join-Path $PSScriptRoot "sync-brand-assets.ps1")) {
    Write-Host "Syncing STWL brand assets..."
    & (Join-Path $PSScriptRoot "sync-brand-assets.ps1")
}

$extras = "[dev]"
if ($IncludeOcr) {
    $extras = "[dev,ocr]"
}

Write-Host "Reinstalling Python package $extras..."
pip install -e "$repo$extras"

$nodeTools = Get-RoadHawkNodeTools
Write-Host "Refreshing web dependencies with Node at $($nodeTools.NodeDir)..."
Set-Location (Join-Path $repo "web")
if ($ProductionWeb) {
    & $nodeTools.NpmCmd ci
    & $nodeTools.NpmCmd run build
} else {
    & $nodeTools.NpmCmd install
}

Set-Location $repo

if (-not $SkipTests) {
    Write-Host "Running pytest..."
    python -m pytest -q
}

$version = python -c "from road_hawk.version import version_info; import json; print(json.dumps(version_info()))"
Write-Host ""
Write-Host "Update complete: $version"
Write-Host "Restart services if they are already running:"
Write-Host "  API:  .\scripts\start-api.ps1"
Write-Host "  Web:  .\scripts\start-web.ps1"
if ($ProductionWeb) {
    Write-Host "  Prod: cd web; npm run start"
}