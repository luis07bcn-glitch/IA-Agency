# Lanza el bot (paper) y el dashboard en segundo plano, sin duplicar procesos.
# Pensado para ejecutarse al iniciar sesión de Windows (carpeta Inicio) o a mano.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path       # ...\polymarket-bot
$repo = Split-Path -Parent $root                              # ...\IA-Agency
$py = Join-Path $repo "venv\Scripts\python.exe"
$streamlit = Join-Path $repo "venv\Scripts\streamlit.exe"
$logs = Join-Path $root "logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$bot = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'run_bot\.py' }
if ($bot) {
    Write-Host "Bot ya corriendo (PID $($bot.ProcessId)), no se relanza."
} else {
    Start-Process -FilePath $py -ArgumentList "`"$root\run_bot.py`"" `
        -WorkingDirectory $repo -WindowStyle Hidden `
        -RedirectStandardOutput "$logs\bot_$stamp.log" `
        -RedirectStandardError "$logs\bot_$stamp.err.log"
    Write-Host "Bot lanzado. Log: $logs\bot_$stamp.log"
}

$dash = Get-CimInstance Win32_Process -Filter "Name='streamlit.exe'" |
    Where-Object { $_.CommandLine -match 'polymarket-bot' }
if ($dash) {
    Write-Host "Dashboard ya corriendo (PID $($dash.ProcessId)), no se relanza."
} else {
    Start-Process -FilePath $streamlit `
        -ArgumentList "run `"$root\dashboard\app.py`" --server.port 8507 --server.headless true" `
        -WorkingDirectory $repo -WindowStyle Hidden `
        -RedirectStandardOutput "$logs\dashboard_$stamp.log" `
        -RedirectStandardError "$logs\dashboard_$stamp.err.log"
    Write-Host "Dashboard lanzado: http://localhost:8507"
}
