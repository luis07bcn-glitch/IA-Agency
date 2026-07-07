# Detiene el bot y el dashboard. El estado queda a salvo en SQLite.
$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='streamlit.exe'" |
    Where-Object { $_.CommandLine -match 'run_bot\.py|polymarket-bot' }
if (-not $procs) {
    Write-Host "No hay procesos del bot corriendo."
} else {
    foreach ($p in $procs) {
        Write-Host "Deteniendo PID $($p.ProcessId): $($p.Name)"
        Stop-Process -Id $p.ProcessId -Force -Confirm:$false
    }
    Write-Host "Hecho. Los trades abiertos se liquidarán al relanzar."
}
