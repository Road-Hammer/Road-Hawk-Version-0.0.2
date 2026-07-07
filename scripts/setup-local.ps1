# First-time setup for Road Hawk on D:
$repo = Split-Path $PSScriptRoot -Parent
$web = Join-Path $repo "web"

$nodePaths = @(
    "C:\Program Files\nodejs",
    "$env:LOCALAPPDATA\road-hawk-node"
)
foreach ($dir in $nodePaths) {
    if (Test-Path "$dir\node.exe") {
        $env:PATH = "$dir;$env:PATH"
        break
    }
}

Write-Host "Installing Python package..."
pip install -e $repo

Write-Host "Installing web dependencies..."
Set-Location $web
if (Test-Path "node_modules") {
    Remove-Item "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
}
npm install

Write-Host "Done. Start with:"
Write-Host "  API:  .\scripts\start-api.ps1"
Write-Host "  Web:  .\scripts\start-web.ps1"