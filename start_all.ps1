# MerakIA — Arranca todos los servicios en ventanas separadas

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root "venv\Scripts"

Write-Host "Arrancando servicios MerakIA..." -ForegroundColor Cyan

# Plataforma MerakIA + Prospector (puerto 8506)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Plataforma MerakIA — http://localhost:8506' -ForegroundColor Green; & '$venv\streamlit.exe' run app.py --server.port 8506" `
    -WindowStyle Normal

# ChefMenu AI (puerto 8503)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'ChefMenu AI — http://localhost:8503' -ForegroundColor Green; & '$venv\streamlit.exe' run chefmenu\app.py --server.port 8503" `
    -WindowStyle Normal

# Financial Analyzer (puerto 8504)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Financial Analyzer — http://localhost:8504' -ForegroundColor Green; & '$venv\streamlit.exe' run financial_analyzer\dashboard\app.py --server.port 8504" `
    -WindowStyle Normal

# Web MerakIA Next.js (puerto 3860)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\merakia-web'; Write-Host 'Web MerakIA — http://localhost:3860' -ForegroundColor Green; npm run dev -- -p 3860" `
    -WindowStyle Normal

Write-Host ""
Write-Host "Servicios iniciados:" -ForegroundColor Cyan
Write-Host "  Plataforma MerakIA       -> http://localhost:8506" -ForegroundColor Yellow
Write-Host "  ChefMenu AI              -> http://localhost:8503" -ForegroundColor Yellow
Write-Host "  Financial Analyzer       -> http://localhost:8504" -ForegroundColor Yellow
Write-Host "  Web MerakIA              -> http://localhost:3860" -ForegroundColor Yellow

# Esperar a que la plataforma principal este lista y abrir el navegador
Write-Host ""
Write-Host "Esperando a que la plataforma principal arranque..." -ForegroundColor Cyan
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8506" -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { break }
    } catch { }
}
Start-Process "http://localhost:8506"
Write-Host "Navegador abierto en la plataforma MerakIA." -ForegroundColor Green
