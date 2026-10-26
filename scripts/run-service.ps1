param([Parameter(Mandatory=$true)][ValidateSet('api','worker','web')][string]$Service)
$ErrorActionPreference = 'Stop'
$ProjectPath = Split-Path -Parent $PSScriptRoot
if ($Service -eq 'web') {
    Set-Location -LiteralPath (Join-Path $ProjectPath 'frontend')
    & npm.cmd run dev
} else {
    Set-Location -LiteralPath (Join-Path $ProjectPath 'backend')
    $LocalPython = Join-Path $ProjectPath '.venv\Scripts\python.exe'
    if ($Service -eq 'api') { & $LocalPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload }
    else { & $LocalPython -m app.worker }
}
