$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$env:OLLAMA_URL = 'http://127.0.0.1:11436'
$env:OLLAMA_MODEL = 'ministral-3:8b'
& .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 9002
