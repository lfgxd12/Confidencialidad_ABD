"""Laboratorio: ejecuta los scripts .sql del repositorio desde la web.

MODELO DE SEGURIDAD (leer antes de tocar):
  * Solo corre scripts de una LISTA BLANCA (LAB_SCRIPTS). No existe endpoint que reciba SQL libre.
  * Esta apagado por defecto: requiere LAB_ENABLED=true y SYS_PASSWORD en panel/.env.
  * Cada ejecucion exige confirmacion escrita ("EJECUTAR <id>") y se rechaza si el servicio
    conectado no es el PDB esperado (LAB_EXPECTED_CON, por defecto XEPDB1).
  * El panel solo escucha en 127.0.0.1 y rechaza cabeceras Host ajenas (ver main.py).
  * Cada corrida se guarda en evidencias/panel/<id>_<fecha>.log; nunca sobrescribe los logs originales.

El analizador imita lo minimo de SQL*Plus que usan NUESTROS scripts: SET, SPOOL, COLUMN, PROMPT, EXEC.
No implementa bloques PL/SQL con '/' (los scripts no los usan); si aparece uno, se rechaza.
"""
import re
import threading
from datetime import datetime

from . import config

LAB_DIR_LOGS = config.EVID_DIR / "panel"

# id -> metadatos. `como`: sys | auditor | analista. `modifica`: True si cambia la base.
LAB_SCRIPTS = {
    "00":  dict(file="00_crear_auditor.sql", como="sys", modifica=True, titulo="Crear usuario auditor",
                efecto="Crea CONF_AUDITOR (solo lectura de catalogo).", requiere=[], revierte="07"),
    "00b": dict(file="00b_ajuste_auditor.sql", como="sys", modifica=True, titulo="Ajuste del auditor",
                efecto="GRANT SELECT sobre DBA_USERS_WITH_DEFPWD a CONF_AUDITOR.", requiere=["00"], revierte="07"),
    "01":  dict(file="01_privilegios_roles.sql", como="auditor", modifica=False, titulo="OBS-01..06 Privilegios y roles",
                efecto="Solo lectura.", requiere=["00", "00b"], revierte=None),
    "02":  dict(file="02_autenticacion_perfiles.sql", como="auditor", modifica=False, titulo="OBS-07..09 Autenticacion y perfiles",
                efecto="Solo lectura.", requiere=["00", "00b"], revierte=None),
    "03":  dict(file="03_cifrado_red.sql", como="auditor", modifica=False, titulo="OBS-10..11 Cifrado y red",
                efecto="Solo lectura.", requiere=["00", "00b"], revierte=None),
    "04":  dict(file="04_masking_demo.sql", como="sys", modifica=True, titulo="Esquema demo de masking",
                efecto="Crea CONF_DEMO (tabla con 3 filas, vista enmascarada), rol y usuario CONF_ANALISTA.", requiere=[], revierte="07"),
    "05a": dict(file="05a_politicas_auditoria.sql", como="sys", modifica=True, titulo="Politicas de auditoria",
                efecto="Crea y habilita POL_CONF_CLIENTES y POL_CONF_PRIVILEGIADOS.", requiere=["04"], revierte="07"),
    "05c": dict(file="05c_pruebas_analista.sql", como="analista", modifica=False, titulo="Pruebas como CONF_ANALISTA",
                efecto="Dos SELECT: la vista (ok) y la tabla base (debe dar ORA-00942).", requiere=["04", "05a"], revierte=None),
    "05b": dict(file="05b_consulta_auditoria.sql", como="sys", modifica=True, titulo="Consulta de la pista de auditoria",
                efecto="Vacia a disco la pista (FLUSH) y consulta.", requiere=["05a", "05c"], revierte=None),
    "05d": dict(file="05d_prueba_privilegiados.sql", como="sys", modifica=True, titulo="Prueba de acciones privilegiadas",
                efecto="Crea y elimina CONF_PRUEBA para generar eventos auditados.", requiere=["05a"], revierte="se autoelimina"),
    "06":  dict(file="06_respaldos_logs_parcheo.sql", como="auditor", modifica=False, titulo="Respaldos, logs y parches",
                efecto="Solo lectura.", requiere=["00", "00b"], revierte=None),
    "08":  dict(file="08_matriz_evaluacion.sql", como="auditor", modifica=False, titulo="Matriz de evaluacion (15 criterios)",
                efecto="Solo lectura.", requiere=["00", "00b"], revierte=None),
    "07":  dict(file="07_limpieza_demo.sql", como="sys", modifica=True, titulo="LIMPIEZA: elimina todo lo creado",
                efecto="Elimina politicas, CONF_ANALISTA, CONF_DEMO (CASCADE) y CONF_AUDITOR.", requiere=[], revierte="00, 04, 05a"),
}
ORDEN = ["00", "00b", "01", "02", "03", "04", "05a", "05c", "05b", "05d", "06", "08", "07"]

_lock = threading.Lock()


def habilitado() -> bool:
    return config.LAB_ENABLED and bool(config.SYS_PASSWORD)


def catalogo() -> list[dict]:
    return [{"id": i, **{k: v for k, v in LAB_SCRIPTS[i].items() if k != "file"},
             "archivo": LAB_SCRIPTS[i]["file"]} for i in ORDEN]


# ---------------------------------------------------------------- analizador
def _partir(texto: str) -> list[str]:
    """Divide en sentencias por ';' fuera de comillas y comentarios. Lineas SQL*Plus se tratan aparte."""
    out, buf, i, n = [], [], 0, len(texto)
    q = None  # comilla abierta
    while i < n:
        c = texto[i]
        if q:
            buf.append(c)
            if c == q:
                q = None
            i += 1
            continue
        if c in ("'", '"'):
            q = c; buf.append(c); i += 1; continue
        if texto.startswith("--", i):
            j = texto.find("\n", i)
            i = n if j < 0 else j
            continue
        if texto.startswith("/*", i):
            j = texto.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == ";":
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []; i += 1; continue
        buf.append(c); i += 1
    resto = "".join(buf).strip()
    if resto:
        out.append(resto)
    return out


def _cerrado(texto: str) -> bool:
    """True si el texto acumulado termina en ';' (fuera de comillas/comentarios), o esta vacio."""
    i, n, q, ultimo = 0, len(texto), None, ""
    while i < n:
        c = texto[i]
        if q:
            if c == q:
                q = None
            ultimo = c; i += 1; continue
        if c in ("'", '"'):
            q = c; ultimo = c; i += 1; continue
        if texto.startswith("--", i):
            j = texto.find("\n", i); i = n if j < 0 else j; continue
        if texto.startswith("/*", i):
            j = texto.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        if not c.isspace():
            ultimo = c
        i += 1
    return q is None and ultimo in ("", ";")


_SQLPLUS = re.compile(r"^(SET|SPOOL|COLUMN|PROMPT|EXEC|EXECUTE)\b", re.I)


def analizar(texto: str) -> list[dict]:
    """Devuelve [{tipo: 'sql'|'prompt'|'ignorar'|'exec', texto}] en orden.

    Las lineas SQL*Plus no llevan ';' y terminan en el salto de linea, asi que se
    separan primero y el resto se parte por ';'.
    """
    items, sql_lineas = [], []

    def vaciar():
        if sql_lineas:
            for s in _partir("\n".join(sql_lineas)):
                items.append({"tipo": "sql", "texto": s})
            sql_lineas.clear()

    en_bloque = False
    for linea in texto.splitlines():
        s = linea.strip()
        if en_bloque:
            sql_lineas.append(linea)
            if "*/" in s:
                en_bloque = False
            continue
        if s.startswith("/*") and "*/" not in s:
            en_bloque = True; sql_lineas.append(linea); continue
        if not s or s.startswith("--"):
            continue
        if s == "/" or re.match(r"^(BEGIN|DECLARE)\b", s, re.I):
            raise ValueError("Bloques PL/SQL no soportados por el laboratorio: " + s[:40])
        m = _SQLPLUS.match(s)
        if m and _cerrado("\n".join(sql_lineas)):
            k = m.group(1).upper()
            resto = s[m.end():].strip().rstrip(";")
            if k == "PROMPT":
                vaciar(); items.append({"tipo": "prompt", "texto": resto})
            elif k in ("EXEC", "EXECUTE"):
                vaciar(); items.append({"tipo": "exec", "texto": "BEGIN " + resto + "; END;"})
            else:
                vaciar(); items.append({"tipo": "ignorar", "texto": s})
            continue
        sql_lineas.append(linea)
    vaciar()
    return items


# ---------------------------------------------------------------- ejecucion
def _tabla(cols: list[str], filas: list[tuple]) -> str:
    datos = [["" if v is None else str(v) for v in f] for f in filas]
    anchos = [max([len(c)] + [len(r[i]) for r in datos]) for i, c in enumerate(cols)]
    lin = lambda r: "  ".join(v.ljust(anchos[i]) for i, v in enumerate(r)).rstrip()
    return "\n".join([lin(cols), "  ".join("-" * a for a in anchos)] + [lin(r) for r in datos])


def ejecutar_items(cur, items: list[dict]) -> str:
    """Corre los items con un cursor. Un error no detiene el resto (como SQL*Plus por defecto)."""
    sal = []
    for it in items:
        t, x = it["tipo"], it["texto"]
        if t == "ignorar":
            continue
        if t == "prompt":
            sal.append(x); continue
        resumen = " ".join(x.split())[:110]
        sal.append(f"\nSQL> {resumen}")
        try:
            cur.execute(x)
            if cur.description:
                cols = [d[0] for d in cur.description]
                filas = cur.fetchall()
                sal.append(_tabla(cols, filas) if filas else "ninguna fila seleccionada")
                sal.append(f"\n{len(filas)} fila(s) seleccionada(s).")
            else:
                sal.append("OK" if t == "exec" or cur.rowcount in (None, -1) else f"{cur.rowcount} fila(s) afectada(s).")
        except Exception as e:  # ORA-xxxxx: se muestra y se continua
            sal.append(f"ERROR: {str(e).strip()}")
    return "\n".join(sal)


def _credenciales(como: str) -> dict:
    if como == "sys":
        return dict(user="SYS", password=config.SYS_PASSWORD, sysdba=True)
    if como == "auditor":
        return dict(user=config.ORACLE_USER or "conf_auditor", password=config.ORACLE_PASSWORD or "Conf_Auditor#2026", sysdba=False)
    if como == "analista":
        return dict(user="conf_analista", password=config.ANALISTA_PASSWORD, sysdba=False)
    raise ValueError(como)


def conectar(como: str):
    import oracledb
    c = _credenciales(como)
    kw = dict(user=c["user"], password=c["password"], dsn=config.ORACLE_DSN)
    if c["sysdba"]:
        kw["mode"] = oracledb.AUTH_MODE_SYSDBA
    return oracledb.connect(**kw)


def ejecutar(id_: str, conectar_fn=None, ahora=None) -> dict:
    meta = LAB_SCRIPTS.get(id_)
    if not meta:
        raise KeyError(id_)
    if not habilitado():
        raise RuntimeError("Laboratorio deshabilitado: define LAB_ENABLED=true y SYS_PASSWORD en panel/.env")
    items = analizar((config.SCRIPTS_DIR / meta["file"]).read_text(encoding="utf-8"))
    conectar_fn = conectar_fn or conectar
    if not _lock.acquire(blocking=False):
        raise RuntimeError("Ya hay un script en ejecucion; espera a que termine")
    try:
        with conectar_fn(meta["como"]) as con:
            cur = con.cursor()
            cur.execute("SELECT USER, SYS_CONTEXT('USERENV','CON_NAME') FROM dual")
            usuario, con_name = cur.fetchone()
            if config.EXPECTED_CON and (con_name or "").upper() != config.EXPECTED_CON.upper():
                raise RuntimeError(f"Conectado a {con_name}, se esperaba {config.EXPECTED_CON}. No se ejecuta nada.")
            ts = (ahora or datetime.now().astimezone())
            enc = (f"-- Panel de laboratorio · script {id_} ({meta['file']})\n"
                   f"-- Usuario: {usuario} · Contenedor: {con_name} · {ts.isoformat(timespec='seconds')}\n")
            cuerpo = ejecutar_items(cur, items)
            if meta["modifica"]:
                con.commit()
    finally:
        _lock.release()
    texto = enc + cuerpo + "\n"
    LAB_DIR_LOGS.mkdir(parents=True, exist_ok=True)
    nombre = f"{id_}_{ts.strftime('%Y%m%d_%H%M%S')}.log"
    (LAB_DIR_LOGS / nombre).write_text(texto, encoding="utf-8")
    return {"id": id_, "usuario": usuario, "contenedor": con_name, "salida": texto,
            "log": f"panel/{nombre}", "errores": cuerpo.count("ERROR:")}


def estado_demo(conectar_fn=None) -> dict:
    """Que objetos del laboratorio existen ahora (consulta de lectura como SYS)."""
    if not habilitado():
        raise RuntimeError("Laboratorio deshabilitado")
    conectar_fn = conectar_fn or conectar
    with conectar_fn("sys") as con:
        cur = con.cursor()
        cur.execute("SELECT username FROM dba_users WHERE username LIKE 'CONF%' ORDER BY 1")
        usuarios = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT policy_name FROM audit_unified_enabled_policies WHERE policy_name LIKE 'POL_CONF%' ORDER BY 1")
        pol = [r[0] for r in cur.fetchall()]
    return {"usuarios": usuarios, "politicas": pol}
