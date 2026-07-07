# Adds common Node.js install locations to the user PATH (idempotent).
$candidates = @(
    "C:\Program Files\nodejs",
    "$env:LOCALAPPDATA\road-hawk-node"
)

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$parts = @($userPath -split ";" | Where-Object { $_ })

foreach ($dir in $candidates) {
    if ((Test-Path "$dir\node.exe") -and ($parts -notcontains $dir)) {
        $parts = @($dir) + $parts
        Write-Host "Added to user PATH: $dir"
    }
}

$newPath = ($parts | Select-Object -Unique) -join ";"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")
$env:PATH = "$newPath;$env:PATH"

Write-Host "User PATH updated. Open a new terminal for system-wide effect."
if (Test-Path "C:\Program Files\nodejs\node.exe") {
    & "C:\Program Files\nodejs\node.exe" --version
} elseif (Test-Path "$env:LOCALAPPDATA\road-hawk-node\node.exe") {
    & "$env:LOCALAPPDATA\road-hawk-node\node.exe" --version
}