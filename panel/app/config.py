"""Rutas y variables de entorno.

Analogia Spring Boot: esto es el application.properties + @ConfigurationProperties.
Los valores sensibles (usuario/clave de Oracle) vienen SOLO del archivo .env del
servidor; el navegador nunca los envia ni los ve.
"""
import os
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = PANEL_DIR.parent


def _load_dotenv() -> None:
    env = PANEL_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

DATA_DIR = PANEL_DIR / "data"
STATIC_DIR = PANEL_DIR / "static"
EVID_DIR = Path(os.getenv("EVID_DIR", REPO_DIR / "evidencias"))
SCRIPTS_DIR = Path(os.getenv("SCRIPTS_DIR", REPO_DIR / "scripts"))

# Conexion en vivo (solo lectura). Si falta algo, el modo en vivo queda deshabilitado.
ORACLE_USER = os.getenv("ORACLE_USER", "")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/XEPDB1")
LIVE_ENABLED = bool(ORACLE_USER and ORACLE_PASSWORD)

# Laboratorio (escritura). Apagado por defecto; ver app/lab.py para el modelo de seguridad.
LAB_ENABLED = os.getenv("LAB_ENABLED", "false").lower() == "true"
SYS_PASSWORD = os.getenv("SYS_PASSWORD", "")
ANALISTA_PASSWORD = os.getenv("ANALISTA_PASSWORD", "Conf_Analista#2026")  # clave de laboratorio, ya publica en el script 04
EXPECTED_CON = os.getenv("LAB_EXPECTED_CON", "XEPDB1")
