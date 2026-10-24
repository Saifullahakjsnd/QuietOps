$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$env:BACKEND_URL = 'http://127.0.0.1:9002'
npm run start
