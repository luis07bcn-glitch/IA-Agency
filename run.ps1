$env:PYTHONUTF8 = "1"

# Sin argumentos → menú de selección
if ($args.Count -eq 0) {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════╗"
    Write-Host "║         MerakIA Agency               ║"
    Write-Host "╠══════════════════════════════════════╣"
    Write-Host "║  1. Agencia principal  (main.py)     ║"
    Write-Host "║  2. ChefMenu AI        (port 8503)   ║"
    Write-Host "║  3. ProspectorIA       (port 8501)   ║"
    Write-Host "║  4. VideoStudio Pro    (port 8502)   ║"
    Write-Host "╚══════════════════════════════════════╝"
    Write-Host ""
    $opcion = Read-Host "Selecciona (1-4)"

    switch ($opcion) {
        "1" { & .\venv\Scripts\python.exe main.py }
        "2" { & .\venv\Scripts\python.exe -m streamlit run chefmenu\app.py --server.port 8503 }
        "3" { & .\venv\Scripts\python.exe -m streamlit run prospectoria\app.py --server.port 8501 }
        "4" { & .\venv\Scripts\python.exe -m streamlit run videostudio\app.py --server.port 8502 }
        default { Write-Host "Opción no válida." }
    }
} else {
    # Con argumento directo: .\run.ps1 chef / prospector / video / main
    switch ($args[0]) {
        "chef"      { & .\venv\Scripts\python.exe -m streamlit run chefmenu\app.py --server.port 8503 }
        "prospector"{ & .\venv\Scripts\python.exe -m streamlit run prospectoria\app.py --server.port 8501 }
        "video"     { & .\venv\Scripts\python.exe -m streamlit run videostudio\app.py --server.port 8502 }
        "main"      { & .\venv\Scripts\python.exe main.py }
        default     { & .\venv\Scripts\python.exe main.py $args }
    }
}
