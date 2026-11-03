param([switch]$RunMeta)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Use the installed checkout with its .venv.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectPath 'frontend\.next\standalone\server.js'))) { throw 'Run npm run build in frontend before starting the recording workspace.' }
foreach ($port in @(13300,18001)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw "Port $port is already in use. Stop that demo before starting another." }
}
$demoRunPath = Join-Path $projectPath ('.jury-demo\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$arguments = @((Join-Path $PSScriptRoot 'prepare-jury-demo.py'),'--directory',$demoRunPath)
if ($RunMeta) { $arguments += '--run-meta' }
& $pythonPath @arguments
if ($LASTEXITCODE -ne 0) { throw 'Demo preparation or real Meta inference failed. No services were started.' }
$receipt = Get-Content -LiteralPath (Join-Path $demoRunPath 'demo-receipt.json') -Raw | ConvertFrom-Json
if (-not $receipt.fictional -or $receipt.institutional_data_used) { throw 'Unexpected demonstration receipt.' }
$nodePath = (Get-Command node.exe).Source
$savedEnvironment = @{}
$demoEnvironment = @{
    LQ_DATABASE_URL = ('sqlite:///' + $receipt.database.Replace('\','/'))
    LQ_STORAGE_DIR = (Join-Path $demoRunPath 'files')
    LQ_SMTP_HOST = ''; LQ_ODK_URL = ''; LQ_COOKIE_SECURE = 'false'
    LQ_ALLOWED_ORIGINS = 'http://127.0.0.1:13300,http://localhost:13300'
    LQ_API_URL = 'http://127.0.0.1:18001'; PORT = '13300'; LQ_WEB_HOST = '127.0.0.1'
    NEXT_TELEMETRY_DISABLED = '1'
}
try {
    foreach ($name in $demoEnvironment.Keys) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name,'Process')
        [Environment]::SetEnvironmentVariable($name,$demoEnvironment[$name],'Process')
    }
    $api = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','18001') -WorkingDirectory (Join-Path $projectPath 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $demoRunPath 'api.log') -RedirectStandardError (Join-Path $demoRunPath 'api-error.log')
    $worker = Start-Process -FilePath $pythonPath -ArgumentList @('-m','app.worker') -WorkingDirectory (Join-Path $projectPath 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $demoRunPath 'worker.log') -RedirectStandardError (Join-Path $demoRunPath 'worker-error.log')
    $web = Start-Process -FilePath $nodePath -ArgumentList @('scripts/start-production.cjs') -WorkingDirectory (Join-Path $projectPath 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $demoRunPath 'web.log') -RedirectStandardError (Join-Path $demoRunPath 'web-error.log')
    @{api=$api.Id;worker=$worker.Id;web=$web.Id} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $demoRunPath 'service-pids.json') -Encoding UTF8
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ($api.HasExited -or $worker.HasExited -or $web.HasExited) { throw "A demo service stopped. See the logs in $demoRunPath" }
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:18001/api/health' -TimeoutSec 1
            $webResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:13300' -UseBasicParsing -TimeoutSec 1
            if ($health.status -eq 'ok' -and $webResponse.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 400
    }
    if (-not $ready) { throw "Demo did not become ready. See the logs in $demoRunPath" }
} catch {
    foreach ($process in @($api,$worker,$web)) {
        if ($process -and -not $process.HasExited) { Stop-Process -InputObject $process -ErrorAction SilentlyContinue }
    }
    throw
} finally {
    foreach ($name in $savedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($name,$savedEnvironment[$name],'Process') }
}
Write-Host 'Fictional jury workspace: http://127.0.0.1:13300'
Write-Host 'Demo-only login: admin@labquality.local / Fictional-recording-only-2026!'
Write-Host "Receipt, evidence and service logs: $demoRunPath"
Write-Host 'Use a separate checkout for the demo and review docs/JURY_REHEARSAL.md before recording.'
