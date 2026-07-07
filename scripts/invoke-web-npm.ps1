function Install-RoadHawkWebDeps {
    param(
        [Parameter(Mandatory = $true)]
        [object]$NodeTools,
        [Parameter(Mandatory = $true)]
        [string]$WebWorkDir,
        [switch]$CleanInstall
    )

    if (-not $CleanInstall -and (Test-RoadHawkWebDepsHealthy -WebWorkDir $WebWorkDir)) {
        Write-Host "Existing web dependencies look healthy; skipping npm ci."
        return
    }

    if ($CleanInstall -or (Test-Path (Join-Path $WebWorkDir "node_modules"))) {
        Reset-RoadHawkWebNodeModules -WebWorkDir $WebWorkDir
    }

    & $NodeTools.NpmCmd ci
    if ($LASTEXITCODE -eq 0) {
        return
    }

    Write-Host "npm ci failed; retrying with a clean node_modules..."
    Reset-RoadHawkWebNodeModules -WebWorkDir $WebWorkDir
    & $NodeTools.NpmCmd ci
    if ($LASTEXITCODE -eq 0) {
        return
    }

    Write-Host "npm ci still failed; falling back to npm install..."
    & $NodeTools.NpmCmd install
    if ($LASTEXITCODE -ne 0) {
        throw @"
npm web install failed (exit $LASTEXITCODE).
Try: .\scripts\push-update.ps1 -Message `"..."` -SkipWebBuild
GitHub Actions will still build the dashboard on push.
"@
    }
}

function Build-RoadHawkWeb {
    param(
        [Parameter(Mandatory = $true)]
        [object]$NodeTools,
        [Parameter(Mandatory = $true)]
        [string]$WebWorkDir
    )

    $webBin = Join-Path $WebWorkDir "node_modules\.bin"
    $nextCmd = Join-Path $webBin "next.cmd"
    $nextCli = Join-Path $WebWorkDir "node_modules\next\dist\bin\next"

    if (Test-Path $webBin) {
        $env:PATH = "$webBin;$($NodeTools.NodeDir);$env:PATH"
    }

    if (Test-Path $nextCmd) {
        Write-Host "Running next build via $nextCmd"
        & $nextCmd build
    } elseif (Test-Path "$nextCli.js") {
        Write-Host "Running next build via node CLI"
        & $NodeTools.NodeExe "$nextCli.js" build
    } else {
        Write-Host "Running next build via npm exec"
        & $NodeTools.NpmCmd exec -- next build
    }

    if ($LASTEXITCODE -ne 0) {
        throw "next build failed with exit code $LASTEXITCODE"
    }
}