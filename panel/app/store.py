"""Capa de datos: lee los JSON de data/ (fuente unica de verdad).

Analogia Spring Boot: un @Repository, pero de solo lectura y sobre archivos.
"""
import json
import re
from functools import lru_cache

from . import config

_NOMBRES = ("riesgos", "tareas", "controles", "observables", "matriz", "pruebas", "hallazgos")


@lru_cache(maxsize=None)
def cargar(nombre: str):
    if nombre not in _NOMBRES:
        raise KeyError(nombre)
    return json.loads((config.DATA_DIR / f"{nombre}.json").read_text(encoding="utf-8"))


_LOG_OK = re.compile(r"^[A-Za-z0-9_]+\.(log|txt)$")


def listar_evidencias() -> list[dict]:
    if not config.EVID_DIR.exists():
        return []
    return [{"nombre": p.name, "bytes": p.stat().st_size}
            for p in sorted(config.EVID_DIR.iterdir())
            if p.is_file() and _LOG_OK.match(p.name)]


def leer_evidencia(nombre: str) -> str:
    """Solo nombres de la lista blanca (patron + existe en la carpeta). Evita ../"""
    if not _LOG_OK.match(nombre):
        raise PermissionError(nombre)
    p = config.EVID_DIR / nombre
    if not p.is_file() or p.parent != config.EVID_DIR:
        raise FileNotFoundError(nombre)
    raw = p.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")
