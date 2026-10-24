$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
# Keep this project's CLI configuration separate from other sessions.
$env:GH_CONFIG_DIR = Join-Path (Get-Location).Path 'data/github-auth'
$env:GH_NO_UPDATE_NOTIFIER = '1'
$env:GH_NO_EXTENSION_UPDATE_NOTIFIER = '1'
& data/tools/github-cli/bin/gh.exe auth login --hostname github.com --git-protocol https --web
