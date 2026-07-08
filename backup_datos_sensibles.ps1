# Copia a OneDrive lo que .gitignore excluye a proposito (claves .env,
# bases de datos locales) para no perderlo si falla el equipo.
# OneDrive se encarga de la sincronizacion en la nube; este script solo
# copia los archivos dentro del repo hacia la carpeta sincronizada.

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$destino = "$env:USERPROFILE\OneDrive\IA-Agency-backup"

$patrones = @("*.env", "*.env.local", "*.db", "*.sqlite", "*.sqlite3", "*.duckdb", "paper_portfolio.json")
$excluir = @("node_modules", ".git", "venv", "__pycache__", ".pnpm-store")

$archivos = Get-ChildItem -Path $repo -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $ruta = $_.FullName
        $incluido = $false
        foreach ($p in $patrones) { if ($_.Name -like $p) { $incluido = $true } }
        if (-not $incluido) { return $false }
        foreach ($ex in $excluir) { if ($ruta -match [regex]::Escape("\$ex\")) { return $false } }
        return $true
    }

$copiados = 0
foreach ($f in $archivos) {
    $relativo = $f.FullName.Substring($repo.Length + 1)
    $destinoArchivo = Join-Path $destino $relativo
    $destinoCarpeta = Split-Path -Parent $destinoArchivo
    New-Item -ItemType Directory -Force -Path $destinoCarpeta | Out-Null
    Copy-Item -Path $f.FullName -Destination $destinoArchivo -Force
    $copiados++
}

# Carpetas completas que tampoco estan en git (assets personales, etc.)
$carpetas = @("assets")
foreach ($c in $carpetas) {
    $origen = Join-Path $repo $c
    if (Test-Path $origen) {
        Copy-Item -Path $origen -Destination (Join-Path $destino $c) -Recurse -Force
        $copiados += (Get-ChildItem -Path $origen -Recurse -File).Count
    }
}

Write-Host "Backup completado: $copiados archivos copiados a $destino" -ForegroundColor Green
Write-Host ("Fecha: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
