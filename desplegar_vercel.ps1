# ============================================================
#  MerakIA — Desplegar la web en Vercel (sin pasar por GitHub)
#  Usa el login de Vercel que ya hiciste. Crea el proyecto,
#  sube las variables de entorno desde .env.local y publica.
#  Ejecuta este script una sola vez para el primer deploy.
#  Para futuros cambios: basta con  vercel --prod  (o re-ejecutar).
# ============================================================

$ErrorActionPreference = "Stop"
$web = "C:\Users\luis0\Documents\IA-Agency\merakia-web"
Set-Location $web

# Asegurar vercel en PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "=== 1/3 . Primer deploy (crea el proyecto en Vercel) ===" -ForegroundColor Cyan
Write-Host "Acepta los valores por defecto (nombre del proyecto: merakia-web)." -ForegroundColor Yellow
vercel --yes

Write-Host "`n=== 2/3 . Subiendo variables de entorno desde .env.local ===" -ForegroundColor Cyan
$envlocal = Join-Path $web ".env.local"
$envs = @("production","preview","development")

if (Test-Path $envlocal) {
    Get-Content $envlocal | ForEach-Object {
        $line = $_.Trim()
        if ($line -and $line -notmatch "^#" -and $line -match "=") {
            $idx  = $line.IndexOf("=")
            $name = $line.Substring(0, $idx).Trim()
            $val  = $line.Substring($idx + 1).Trim().Trim('"')
            if ($name -and $val) {
                foreach ($e in $envs) {
                    # Quita la var si ya existe (ignora error si no estaba) y la vuelve a poner
                    cmd /c "vercel env rm $name $e --yes" 2>$null | Out-Null
                    $val | vercel env add $name $e 2>$null | Out-Null
                }
                Write-Host ("  + " + $name + " anadida (production/preview/development)") -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "  No se encontro .env.local — anade ANTHROPIC_API_KEY manualmente en Vercel." -ForegroundColor Yellow
}

Write-Host "`n=== 3/3 . Deploy a produccion (con las variables ya cargadas) ===" -ForegroundColor Cyan
vercel --prod --yes

Write-Host "`n=== LISTO ===" -ForegroundColor Green
Write-Host "La web esta publicada. La URL aparece arriba (termina en .vercel.app)." -ForegroundColor White
Write-Host "Para cambiar el dominio: vercel.com -> proyecto -> Settings -> Domains" -ForegroundColor White
Write-Host "Para republicar tras un cambio:  cd merakia-web ;  vercel --prod" -ForegroundColor White
