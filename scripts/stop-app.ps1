param([ValidateSet('backend','frontend','both')][string]$Service = 'both')
$ErrorActionPreference = 'Stop'
$quietRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$quietPorts = if ($Service -eq 'backend') { @(9002) } elseif ($Service -eq 'frontend') { @(3002) } else { @(9002,3002) }
foreach ($quietPort in $quietPorts) {
    $quietListener = Get-NetTCPConnection -LocalPort $quietPort -State Listen -ErrorAction SilentlyContinue
    if (-not $quietListener) { continue }
    $quietServer = Get-CimInstance Win32_Process -Filter "ProcessId = $($quietListener.OwningProcess)"
    $quietAncestor = $quietServer
    $quietVerified = $false
    for ($quietDepth = 0; $quietDepth -lt 4 -and $quietAncestor; $quietDepth++) {
        if ($quietAncestor.CommandLine -and $quietAncestor.CommandLine.IndexOf($quietRoot,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) { $quietVerified = $true; break }
        $quietAncestor = Get-CimInstance Win32_Process -Filter "ProcessId = $($quietAncestor.ParentProcessId)" -ErrorAction SilentlyContinue
    }
    if (-not $quietVerified) { throw "Port $quietPort is not verified as this QuietOps workspace. No process stopped." }
    if ($quietPort -eq 9002 -and $quietServer.CommandLine -notlike '*uvicorn backend.main:app*') { throw 'Unexpected backend process. No process stopped.' }
    if ($quietPort -eq 3002 -and $quietServer.CommandLine -notlike '*next*') { throw 'Unexpected frontend process. No process stopped.' }
    Stop-Process -Id $quietServer.ProcessId
    Write-Output "Stopped verified QuietOps process $($quietServer.ProcessId) on port $quietPort."
}
