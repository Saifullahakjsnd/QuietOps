$ErrorActionPreference = 'Stop'
$quietRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $quietRoot
New-Item -ItemType Directory -Force logs | Out-Null
foreach ($quietService in @(@{Name='ollama'; Port=11436}, @{Name='backend'; Port=9002}, @{Name='frontend'; Port=3002})) {
    if (Get-NetTCPConnection -LocalPort $quietService.Port -State Listen -ErrorAction SilentlyContinue) {
        Write-Output "Port $($quietService.Port) is already in use. Leaving the existing process alone."
        continue
    }
    $quietProcess = Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile','-File',"scripts/$($quietService.Name).ps1" -WorkingDirectory $quietRoot -WindowStyle Hidden -RedirectStandardOutput "logs/$($quietService.Name).out.log" -RedirectStandardError "logs/$($quietService.Name).err.log" -PassThru
    Write-Output "$($quietService.Name): launcher PID $($quietProcess.Id), port $($quietService.Port)"
}
Write-Output 'QuietOps: http://127.0.0.1:3002'
