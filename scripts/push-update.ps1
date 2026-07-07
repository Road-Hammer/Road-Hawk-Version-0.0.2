# Maintainer workflow: sync versions, test, commit, and push Road Hawk updates.
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,
    [string]$Branch = "Road-Hawk",
    [switch]$SkipTests,
    [switch]$SkipWebBuild,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

. (Join-Path $PSScriptRoot "ensure-node-path.ps1")
. (Join-Path $PSScriptRoot "ensure-web-workdir.ps1")
. (Join-Path $PSScriptRoot "invoke-web-npm.ps1")

Write-Host "Road Hawk push-update"
Write-Host "Target branch: $Branch"

Write-Host "Syncing version metadata..."
python (Join-Path $PSScriptRoot "sync-version.py")

if (-not $SkipTests) {
    Write-Host "Running pytest..."
    python -m pytest -q
}

if (-not $SkipWebBuild) {
    $nodeTools = Get-RoadHawkNodeTools
    Write-Host "Building web dashboard with Node at $($nodeTools.NodeDir)..."
    & $nodeTools.NodeExe --version

    $webWorkDir = Get-RoadHawkWebWorkDir -RepoRoot $repo
    Set-Location $webWorkDir
    Install-RoadHawkWebDeps -NodeTools $nodeTools -WebWorkDir $webWorkDir
    Build-RoadHawkWeb -NodeTools $nodeTools -WebWorkDir $webWorkDir
    Set-Location $repo
}

$status = git status --porcelain
if (-not $status) {
    Write-Host "No changes to commit."
} else {
    Write-Host "Staging changes..."
    if ($DryRun) {
        git status --short
        Write-Host "Dry run: would commit with message: $Message"
    } else {
        git add -A
        git commit -m $Message
    }
}

if ($DryRun) {
    Write-Host "Dry run: would push to origin/$Branch"
    exit 0
}

Write-Host "Pushing to origin/$Branch..."
git push origin "HEAD:$Branch"

$version = python -c "from road_hawk.version import version_info; import json; print(json.dumps(version_info()))"
Write-Host "Push complete: $version"
Write-Host "GitHub Actions CI will run on the pushed commit."