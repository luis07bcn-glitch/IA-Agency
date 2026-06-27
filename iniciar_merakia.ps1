# ============================================================
#   MerakIA — Lanzador de la plataforma principal
#   Arranca Streamlit, espera a que esté lista y abre el navegador.
# ============================================================

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$streamlit = Join-Path $root "venv\Scripts\streamlit.exe"
$port = 8506
$url = "http://localhost:$port"

if (-not (Test-Path $streamlit)) {
    Write-Host "ERROR: no se encuentra el venv en $streamlit" -ForegroundColor Red
    Write-Host "Crea el entorno con: python -m venv venv  y  venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Pulsa Enter para salir"
    exit 1
}

# ¿Ya está corriendo? Si el puerto responde, solo abrimos el navegador.
$yaActiva = $false
try {
    $r = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $yaActiva = $true }
} catch { }

if ($yaActiva) {
    Write-Host "MerakIA ya esta activa. Abriendo navegador..." -ForegroundColor Green
    Start-Process $url
    exit 0
}

Write-Host "Arrancando MerakIA en $url ..." -ForegroundColor Cyan

# Lanzar Streamlit en segundo plano (sin que abra su propia pestaña)
Start-Process -FilePath $streamlit `
    -ArgumentList "run", "app.py", "--server.port", "$port", "--server.headless", "true" `
    -WorkingDirectory $root `
    -WindowStyle Minimized

# Esperar hasta que el puerto responda (max ~40s)
$listo = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $listo = $true; break }
    } catch { }
}

if ($listo) {
    Write-Host "Lista. Abriendo navegador..." -ForegroundColor Green
    Start-Process $url
} else {
    Write-Host "La plataforma esta tardando mas de lo normal. Abre manualmente: $url" -ForegroundColor Yellow
    Start-Process $url
}
