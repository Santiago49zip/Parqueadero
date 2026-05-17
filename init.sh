#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

python BD/Crear_tablas.py
python BD/fix_schema.py
python BD/Updates.py

echo "Inicialización completa. Ejecuta: python -m backend.app"
