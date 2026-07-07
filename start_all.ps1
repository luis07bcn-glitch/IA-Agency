# MerakIA — Arranca todos los servicios en ventanas separadas

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root "venv\Scripts"

Write-Host "Arrancando servicios MerakIA..." -ForegroundColor Cyan

# Plataforma MerakIA + Prospector + VideoStudio (puerto 8506)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Plataforma MerakIA — http://localhost:8506' -ForegroundColor Green; & '$venv\streamlit.exe' run app.py --server.port 8506" `
    -WindowStyle Minimized

# Paper Trading (puerto 8505)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Paper Trading — http://localhost:8505' -ForegroundColor Green; & '$venv\streamlit.exe' run financial_analyzer\alerts_engine\dashboard_paper_trading.py --server.port 8505" `
    -WindowStyle Minimized

# ChefMenu AI (puerto 8503)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'ChefMenu AI — http://localhost:8503' -ForegroundColor Green; & '$venv\streamlit.exe' run chefmenu\app.py --server.port 8503" `
    -WindowStyle Minimized

# Financial Analyzer (puerto 8504)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Financial Analyzer — http://localhost:8504' -ForegroundColor Green; & '$venv\streamlit.exe' run financial_analyzer\dashboard\app.py --server.port 8504" `
    -WindowStyle Minimized

# Polymarket Bot (puerto 8507)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root'; Write-Host 'Polymarket Bot — http://localhost:8507' -ForegroundColor Green; & '$venv\streamlit.exe' run polymarket-bot\dashboard\app.py --server.port 8507" `
    -WindowStyle Minimized

# Web MerakIA Next.js (puerto 3860) — usa npx next dev (pnpm tiene restricciones de build)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\merakia-web'; Write-Host 'Web MerakIA — http://localhost:3860' -ForegroundColor Green; npx next dev -p 3860" `
    -WindowStyle Minimized

# Agente WhatsApp Citas — API NestJS (3001) + Web Next.js (3010)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\agente-whatsapp-citas'; Write-Host 'Agente Citas API — http://localhost:3001' -ForegroundColor Green; pnpm dev:api" `
    -WindowStyle Minimized
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\agente-whatsapp-citas'; Write-Host 'Agente Citas Web — http://localhost:3010' -ForegroundColor Green; pnpm dev:web" `
    -WindowStyle Minimized

Write-Host ""
Write-Host "Servicios iniciados (ventanas minimizadas):" -ForegroundColor Cyan
Write-Host "  Plataforma MerakIA       -> http://localhost:8506" -ForegroundColor Yellow
Write-Host "  Paper Trading            -> http://localhost:8505" -ForegroundColor Yellow
Write-Host "  Financial Analyzer       -> http://localhost:8504" -ForegroundColor Yellow
Write-Host "  ChefMenu AI              -> http://localhost:8503" -ForegroundColor Yellow
Write-Host "  Polymarket Bot           -> http://localhost:8507" -ForegroundColor Yellow
Write-Host "  Web MerakIA              -> http://localhost:3860" -ForegroundColor Yellow
Write-Host "  Agente Citas (web)       -> http://localhost:3010" -ForegroundColor Yellow
Write-Host "  Agente Citas (api)       -> http://localhost:3001" -ForegroundColor Yellow

# Esperar a que la plataforma principal esté lista y abrir el navegador
Write-Host ""
Write-Host "Esperando a que la plataforma principal arranque (~15s)..." -ForegroundColor Cyan
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8506" -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { break }
    } catch { }
}
Start-Process "http://localhost:8506"
Write-Host "Navegador abierto en la plataforma MerakIA." -ForegroundColor Green
