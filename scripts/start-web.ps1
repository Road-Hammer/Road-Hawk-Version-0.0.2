$systemNode = "C:\Program Files\nodejs"
$portableNode = "$env:LOCALAPPDATA\road-hawk-node"
$webDir = Join-Path $PSScriptRoot "..\web"

if (Test-Path "$systemNode\node.exe") {
    $env:PATH = "$systemNode;$env:PATH"
} elseif (Test-Path "$portableNode\node.exe") {
    $env:PATH = "$portableNode;$env:PATH"
}

Set-Location $webDir
npm run dev