# Stop stale dev servers, clear Next cache, and start fresh.
$webDir = Join-Path $PSScriptRoot "..\web"

Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
        if ($_ -gt 0) {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process on port 3000: $_"
        }
    }

$nextCache = Join-Path $webDir ".next"
if (Test-Path $nextCache) {
    Remove-Item -Recurse -Force $nextCache
    Write-Host "Cleared $nextCache"
}

Start-Process -FilePath (Join-Path $webDir "dev.cmd") -WorkingDirectory $webDir
Write-Host "Road Hawk web UI starting at http://localhost:3000"