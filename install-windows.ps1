param(
    [string]$TargetPath = 'D:\irzelindo\Documentos Pessoais\Candidaturas\Meta Hackathon\hackathon',
    [switch]$Start
)
$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "O comando terminou com erro: $Program (codigo $LASTEXITCODE)" }
}
$SourcePath = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
$TargetPath = [IO.Path]::GetFullPath($TargetPath).TrimEnd('\')
if ($SourcePath -ne $TargetPath) {
    if ($TargetPath.StartsWith($SourcePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'O destino nao pode ficar dentro da pasta de origem.' }
    if ((Test-Path -LiteralPath $TargetPath) -and (Get-ChildItem -LiteralPath $TargetPath -Force | Select-Object -First 1)) {
        throw "O destino ja contem ficheiros. Nada foi substituido: $TargetPath. Extraia o pacote para uma pasta vazia ou execute este instalador dentro do proprio destino."
    }
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Get-ChildItem -LiteralPath $SourcePath -Force | Where-Object { $_.Name -notin @('.env','.venv','node_modules','.next','.git','storage','backups') } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $TargetPath -Recurse
    }
}
Write-Host "Projecto: $TargetPath"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Instale Node.js 22 ou superior e volte a executar o instalador.' }
$NodeMajor = [int]((& node --version).TrimStart('v').Split('.')[0])
if ($NodeMajor -lt 22) { throw 'Este projecto requer Node.js 22 ou superior.' }
$NpmPath = (Get-Command npm.cmd -ErrorAction Stop).Source
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
$PythonPrefix = @()
if ($PythonCommand) { $PythonPath = $PythonCommand.Source }
else {
    $PythonCommand = Get-Command py -ErrorAction Stop
    $PythonPath = $PythonCommand.Source
    $PythonPrefix = @('-3')
}
Invoke-Checked -Program $PythonPath -Arguments ($PythonPrefix + @('-c', 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 ou superior necessario"'))
$ConfigPath = Join-Path $TargetPath '.env'
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    $Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $Bytes = New-Object byte[] 24
        $Generator.GetBytes($Bytes)
        $DemoPassword = [Convert]::ToBase64String($Bytes)
        $Generator.GetBytes($Bytes)
        $DatabasePassword = -join ($Bytes | ForEach-Object { $_.ToString('x2') })
    } finally { $Generator.Dispose() }
    $Content = [IO.File]::ReadAllText((Join-Path $TargetPath '.env.example'))
    $Content = $Content.Replace('LQ_DEMO_PASSWORD=', 'LQ_DEMO_PASSWORD=' + $DemoPassword)
    $Content = $Content.Replace('POSTGRES_PASSWORD=', 'POSTGRES_PASSWORD=' + $DatabasePassword)
    [IO.File]::WriteAllText($ConfigPath, $Content, ([System.Text.UTF8Encoding]::new($false)))
}
$Venv = Join-Path $TargetPath '.venv'
if (-not (Test-Path -LiteralPath (Join-Path $Venv 'Scripts\python.exe'))) {
    Invoke-Checked -Program $PythonPath -Arguments ($PythonPrefix + @('-m','venv',$Venv))
}
$LocalPython = Join-Path $Venv 'Scripts\python.exe'
$Backend = Join-Path $TargetPath 'backend'
Invoke-Checked -Program $LocalPython -Arguments @('-m','pip','install','-r',(Join-Path $Backend 'requirements.lock'))
& (Join-Path $TargetPath 'scripts\repair-sqlalchemy-windows.ps1')
Push-Location -LiteralPath $Backend
try {
    Invoke-Checked -Program $LocalPython -Arguments @('-m','app.bootstrap','--demo')
    Invoke-Checked -Program $LocalPython -Arguments @('-m','pytest','-q')
} finally { Pop-Location }
Push-Location -LiteralPath (Join-Path $TargetPath 'frontend')
try {
    Invoke-Checked -Program $NpmPath -Arguments @('ci','--no-audit','--no-fund')
    Invoke-Checked -Program $NpmPath -Arguments @('run','typecheck')
} finally { Pop-Location }
Write-Host ''
Write-Host 'Instalacao concluida. A palavra-passe local esta em .env, campo LQ_DEMO_PASSWORD.'
Write-Host 'Conta inicial: admin@labquality.local'
Write-Host 'Para iniciar: execute .\start-windows.ps1 dentro do directorio do projecto.'
if ($Start) { & (Join-Path $TargetPath 'start-windows.ps1') }
