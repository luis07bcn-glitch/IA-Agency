# ============================================================
#  MerakIA — Conectar la web a GitHub (paso final)
#  Ejecuta este script una sola vez. Te pedirá login en el
#  navegador (igual que vercel login) y dejará el repo subido.
# ============================================================

$ErrorActionPreference = "Stop"
$web = Join-Path $PSScriptRoot "merakia-web"

# Asegurar gh en el PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "=== 1/3 · Login en GitHub ===" -ForegroundColor Cyan
$logged = $false
try { gh auth status 2>$null; if ($LASTEXITCODE -eq 0) { $logged = $true } } catch {}

if (-not $logged) {
    Write-Host "Se abrira el navegador para autorizar GitHub CLI." -ForegroundColor Yellow
    Write-Host "Elige: GitHub.com  ->  HTTPS  ->  Login with a web browser" -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web
} else {
    Write-Host "Ya estabas autenticado en GitHub." -ForegroundColor Green
}

Write-Host "`n=== 2/3 · Crear repo y subir la web ===" -ForegroundColor Cyan
Set-Location $web

# Crea el repo PRIVADO en tu cuenta y hace push del commit ya preparado
gh repo create merakia-web --private --source "." --remote origin --push

Write-Host "`n=== 3/3 · Conectar con Vercel ===" -ForegroundColor Cyan
Write-Host "Repo subido. Ahora:" -ForegroundColor Green
Write-Host "  1. Entra en https://vercel.com/new" -ForegroundColor White
Write-Host "  2. Importa el repositorio 'merakia-web'" -ForegroundColor White
Write-Host "  3. En Environment Variables anade:" -ForegroundColor White
Write-Host "       ANTHROPIC_API_KEY = (tu clave del archivo .env)" -ForegroundColor White
Write-Host "  4. Deploy. A partir de ahi, cada cambio se publica solo." -ForegroundColor White
Write-Host ""
Write-Host "URL del repo:" -ForegroundColor Cyan
gh repo view --web
