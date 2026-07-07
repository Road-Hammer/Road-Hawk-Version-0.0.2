function Install-RoadHawkWebDeps {
    param(
        [Parameter(Mandatory = $true)]
        [object]$NodeTools,
        [Parameter(Mandatory = $true)]
        [string]$WebWorkDir,
        [switch]$CleanInstall
    )

    if ($CleanInstall) {
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
    if (Test-Path $webBin) {
        $env:PATH = "$webBin;$env:PATH"
    }

    & $NodeTools.NpmCmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed with exit code $LASTEXITCODE"
    }
}