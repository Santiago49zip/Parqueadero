$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

python -m venv "$root\venv"
. "$root\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r "$root\backend\requirements.txt"

python "$root\BD\Crear_tablas.py"
python "$root\BD\fix_schema.py"
python "$root\BD\Updates.py"

Write-Host "Inicialización completa. Ejecuta: python -m backend.app"
