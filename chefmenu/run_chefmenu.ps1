$venv = Join-Path $PSScriptRoot ".." "venv\Scripts\python.exe"
$app  = Join-Path $PSScriptRoot "app.py"
& $venv -m streamlit run $app --server.port 8503
