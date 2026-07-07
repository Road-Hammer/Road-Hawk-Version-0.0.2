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

function Test-RoadHawkWebDepsHealthy {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WebWorkDir
    )

    $nextCmd = Join-Path $WebWorkDir "node_modules\.bin\next.cmd"
    $nextPkg = Join-Path $WebWorkDir "node_modules\next\package.json"
    return (Test-Path $nextCmd) -and (Test-Path $nextPkg)
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
    if (-not (Test-Path $nodeModules)) {
        return
    }

    $stamp = Get-Date -Format "yyyyMMddHHmmss"
    $emptyDir = Join-Path $WebWorkDir ".empty.$stamp"
    New-Item -ItemType Directory -Path $emptyDir -Force | Out-Null
    Write-Host "rmdir incomplete; mirroring empty dir over node_modules..."
    cmd /c "robocopy `"$emptyDir`" `"$nodeModules`" /MIR /NFL /NDL /NJH /NJS /nc /ns /np"
    Remove-Item -LiteralPath $emptyDir -Recurse -Force -ErrorAction SilentlyContinue
    cmd /c "rmdir /s /q `"$nodeModules`""
    if (-not (Test-Path $nodeModules)) {
        return
    }

    $quarantineName = "node_modules.quarantine.$stamp"
    Write-Host "robocopy cleanup failed; quarantining node_modules to $quarantineName..."
    try {
        Rename-Item -LiteralPath $nodeModules -NewName $quarantineName -Force
    } catch {
        throw @"
Could not remove or quarantine node_modules.
Stop Road Hawk web/API terminals and anything using C:\rh-web or port 3000, then retry.
Or use: .\scripts\push-update.ps1 -Message `"..."` -SkipWebBuild
$($_.Exception.Message)
"@
    }
}