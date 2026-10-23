@echo off
REM Arranca el panel en http://127.0.0.1:8000  (solo accesible desde este equipo)
cd /d %~dp0
if not exist .venv ( py -m venv .venv && .venv\Scripts\pip install -r requirements.txt )
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
