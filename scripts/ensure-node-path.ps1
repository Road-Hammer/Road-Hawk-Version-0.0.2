function Get-RoadHawkNodeTools {
    $candidates = @(
        "C:\Program Files\nodejs",
        "$env:LOCALAPPDATA\road-hawk-node"
    )
    if ($env:ProgramFiles) {
        $candidates += Join-Path $env:ProgramFiles "nodejs"
    }

    foreach ($dir in ($candidates | Select-Object -Unique)) {
        $nodeExe = Join-Path $dir "node.exe"
        $npmCmd = Join-Path $dir "npm.cmd"
        if ((Test-Path $nodeExe) -and (Test-Path $npmCmd)) {
            if ($env:PATH -notlike "$dir*") {
                $env:PATH = "$dir;$env:PATH"
            }
            return [PSCustomObject]@{
                NodeDir = $dir
                NodeExe = $nodeExe
                NpmCmd = $npmCmd
            }
        }
    }

    throw "Node.js not found. Install Node.js or run .\scripts\repair-node-path.ps1"
}