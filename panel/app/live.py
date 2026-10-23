"""Modo en vivo: ejecuta, en SOLO LECTURA, la consulta de scripts/08_matriz_evaluacion.sql.

Decision de diseno: no se duplica el SQL. Se extrae del propio script 08 (la
sentencia WITH ... ORDER BY ctl) para que el .sql del repo y el panel no puedan
diverger. Los comandos de SQL*Plus/SQL Developer (SET, SPOOL, COLUMN) no los
entiende un driver, por eso se descartan.

Seguridad: no hay endpoint que reciba SQL. Solo se ejecuta esta sentencia, y la
sesion se abre con la cuenta de auditoria del .env.
"""
import re

from . import config


def extraer_consulta(sql_texto: str) -> str:
    m = re.search(r"^\s*WITH\s+r\s+AS\b.*?;\s*$", sql_texto, re.S | re.M | re.I)
    if not m:
        raise ValueError("No se encontro la sentencia WITH en el script 08")
    stmt = m.group(0).strip()
    stmt = stmt[:-1].rstrip()  # el driver no admite ';' final
    palabras_prohibidas = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|MERGE)\b", re.I)
    if palabras_prohibidas.search(stmt):
        raise ValueError("La sentencia contiene palabras de escritura; no se ejecuta")
    return stmt


def consulta_08() -> str:
    return extraer_consulta((config.SCRIPTS_DIR / "08_matriz_evaluacion.sql").read_text(encoding="utf-8"))


def conectar():
    import oracledb  # import tardio: el modo evidencia no lo necesita
    return oracledb.connect(user=config.ORACLE_USER, password=config.ORACLE_PASSWORD,
                            dsn=config.ORACLE_DSN)


def ejecutar(conectar_fn=None) -> dict:
    """Devuelve {usuario, contenedor, filas:[{ctl,evidencia,criterio,estado}]}."""
    if not config.LIVE_ENABLED:
        raise RuntimeError("Modo en vivo deshabilitado: falta ORACLE_USER/ORACLE_PASSWORD en .env")
    sql = consulta_08()
    conectar_fn = conectar_fn or conectar  # se resuelve al llamar (permite sustituirla en pruebas)
    with conectar_fn() as con:
        con.autocommit = False
        cur = con.cursor()
        cur.execute("SELECT USER, SYS_CONTEXT('USERENV','CON_NAME') FROM dual")
        usuario, contenedor = cur.fetchone()
        cur.execute(sql)
        filas = [{"ctl": a, "evidencia": b, "criterio": int(c), "estado": d}
                 for a, b, c, d in cur.fetchall()]
    return {"usuario": usuario, "contenedor": contenedor, "filas": filas}
