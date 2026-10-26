$ErrorActionPreference = 'Stop'
foreach ($Port in @(8000, 3000)) {
    $InUse = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($InUse) { throw "A porta $Port ja esta em uso. Nenhum processo foi encerrado. Liberte a porta antes de iniciar." }
}
$ServiceScript = Join-Path $PSScriptRoot 'scripts\run-service.ps1'
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'))) { throw 'Execute install-windows.ps1 primeiro.' }
$ShellPath = (Get-Process -Id $PID).Path
foreach ($Service in @('api','worker','web')) {
    Start-Process -FilePath $ShellPath -WorkingDirectory $PSScriptRoot -ArgumentList @('-NoExit','-NoProfile','-File',('"' + $ServiceScript + '"'),'-Service',$Service)
}
Write-Host 'A iniciar API, trabalhador e interface em tres janelas.'
Write-Host 'Abra http://localhost:3000 quando a interface indicar Ready.'
Write-Host 'Para parar, prima Ctrl+C nas tres janelas.'
