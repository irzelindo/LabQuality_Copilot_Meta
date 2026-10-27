$ErrorActionPreference = 'Stop'
$ProjectPath = Split-Path -Parent $PSScriptRoot
$LocalPython = Join-Path $ProjectPath '.venv\Scripts\python.exe'
$RequirementsPath = Join-Path $ProjectPath 'backend\requirements.lock'

if (-not (Test-Path -LiteralPath $LocalPython)) { throw 'Execute install-windows.ps1 primeiro para criar .venv.' }
$PinnedLine = Get-Content -LiteralPath $RequirementsPath | Where-Object { $_ -match '^sqlalchemy==[0-9]+\.[0-9]+\.[0-9]+$' } | Select-Object -First 1
if (-not $PinnedLine) { throw 'Versao fixa do SQLAlchemy nao encontrada em backend\requirements.lock.' }

# An installed native wheel can be blocked by Windows Application Control.
# Test the actual import before replacing it with the official pure-Python build.
& $LocalPython -c 'import sqlalchemy; from sqlalchemy.engine import _util_cy'
if ($LASTEXITCODE -eq 0) {
    Write-Host 'SQLAlchemy carregado. Reparacao desnecessaria.'
    return
}

Write-Host 'A reinstalar SQLAlchemy em Python puro para evitar a extensao bloqueada.'
$Previous = [Environment]::GetEnvironmentVariable('DISABLE_SQLALCHEMY_CEXT', 'Process')
try {
    [Environment]::SetEnvironmentVariable('DISABLE_SQLALCHEMY_CEXT', '1', 'Process')
    & $LocalPython -m pip install --no-cache-dir --no-deps --force-reinstall --no-binary=sqlalchemy $PinnedLine
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar $PinnedLine a partir do codigo-fonte." }
} finally {
    [Environment]::SetEnvironmentVariable('DISABLE_SQLALCHEMY_CEXT', $Previous, 'Process')
}

& $LocalPython -c 'import sqlalchemy; from sqlalchemy.engine import _util_cy; from pathlib import Path; assert Path(_util_cy.__file__).suffix == ".py", _util_cy.__file__; print("SQLAlchemy", sqlalchemy.__version__, "em Python puro")'
if ($LASTEXITCODE -ne 0) { throw 'A importacao do SQLAlchemy em Python puro continua a falhar.' }
