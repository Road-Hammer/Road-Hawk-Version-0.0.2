function Get-RoadHawkWebWorkDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $webDir = (Resolve-Path (Join-Path $RepoRoot "web")).Path

    if (-not ($IsWindows -or $env:OS -match "Windows")) {
        return $webDir
    }

    $junction = "C:\rh-web"
    if (Test-Path $junction) {
        $item = Get-Item -LiteralPath $junction -Force
        $isLink = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        if (-not $isLink) {
            throw "C:\rh-web exists and is not a junction. Remove or rename it, then retry."
        }

        $target = $item.Target
        if ($target -is [array]) {
            $target = $target[0]
        }
        if ($target.TrimEnd("\") -ne $webDir.TrimEnd("\")) {
            Write-Host "Recreating C:\rh-web junction for current repo..."
            cmd /c "rmdir `"$junction`""
            cmd /c "mklink /J `"$junction`" `"$webDir`""
        }
    } else {
        Write-Host "Creating C:\rh-web junction for npm short-path work..."
        cmd /c "mklink /J `"$junction`" `"$webDir`""
    }

    if (-not (Test-Path $junction)) {
        throw "Failed to create C:\rh-web junction."
    }

    Write-Host "Web npm workdir: $junction -> $webDir"
    return $junction
}

function Reset-RoadHawkWebNodeModules {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WebWorkDir
    )

    $nodeModules = Join-Path $WebWorkDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        return
    }

    Write-Host "Removing existing node_modules via short path..."
    cmd /c "rmdir /s /q `"$nodeModules`""
}