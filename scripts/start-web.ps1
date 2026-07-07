$ErrorActionPreference = "Stop"
$systemNode = "C:\Program Files\nodejs"
$portableNode = "$env:LOCALAPPDATA\road-hawk-node"
$altWebDir = "C:\rh-web"
$repoWebDir = Join-Path $PSScriptRoot "..\web"
$webDir = if (Test-Path (Join-Path $repoWebDir "package.json")) { $repoWebDir } elseif (Test-Path (Join-Path $altWebDir "package.json")) { $altWebDir } else { $repoWebDir }
$logFile = Join-Path $PSScriptRoot "web-start.log"

if (Test-Path "$systemNode\node.exe") {
    $env:PATH = "$systemNode;$env:PATH"
} elseif (Test-Path "$portableNode\node.exe") {
    $env:PATH = "$portableNode;$env:PATH"
} else {
    "Node.js not found. Install from https://nodejs.org or use portable node at $portableNode" | Out-File -FilePath $logFile -Encoding utf8
    throw "Node.js not found for Road Hawk web"
}

Set-Location $webDir
"Starting web in $webDir at $(Get-Date -Format o)" | Out-File -FilePath $logFile -Encoding utf8
cmd /c "npm run dev:win -- -p 3000 >> `"$logFile`" 2>&1"