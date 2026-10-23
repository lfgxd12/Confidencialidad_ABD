#!/usr/bin/env bash
# Arranca el panel en http://127.0.0.1:8000  (solo accesible desde este equipo)
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -r requirements.txt; }
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
