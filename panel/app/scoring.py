"""Reglas de calculo. Funciones puras: faciles de probar (ver tests/).

Estas reglas son las del informe (Tabla 5 y Tabla 6): el estado se deriva del
criterio 0-4. No se inventa ninguna metodologia nueva aqui.
"""
from collections import Counter

ESTADOS = ("Cumple", "Parcial", "No cumple")


def estado(criterio: int) -> str:
    """4 = Cumple; 2 y 3 = Parcial; 0 y 1 = No cumple."""
    if criterio is None:
        raise ValueError("criterio vacio")
    if not 0 <= criterio <= 4:
        raise ValueError(f"criterio fuera de rango 0-4: {criterio}")
    if criterio == 4:
        return "Cumple"
    if criterio >= 2:
        return "Parcial"
    return "No cumple"


def nivel_riesgo(impacto: int, probabilidad: int) -> str:
    """I x P: 1-6 Bajo, 7-14 Medio, 15-25 Alto (Seccion 3 del informe)."""
    v = impacto * probabilidad
    return "Alto" if v >= 15 else "Medio" if v >= 7 else "Bajo"


def resumen(filas: list[dict]) -> dict:
    """Conteos y promedio de la matriz."""
    c = Counter(estado(f["criterio"]) for f in filas)
    n = len(filas)
    prom = round(sum(f["criterio"] for f in filas) / n, 2) if n else 0
    return {"total": n, **{e: c.get(e, 0) for e in ESTADOS}, "promedio": prom}


def por_riesgo(filas: list[dict], riesgos: list[dict]) -> list[dict]:
    """Por cada R-CONF: filas asociadas, promedio y el PEOR criterio.

    El semaforo del riesgo usa el peor control (no el promedio) para que un
    control en 0 no quede escondido por otros en 4. Es una regla de
    PRESENTACION del panel; no sustituye a la matriz del informe.
    """
    out = []
    for r in riesgos:
        fs = [f for f in filas if f["riesgo"] == r["id"]]
        if not fs:
            out.append({**r, "filas": 0, "promedio": None, "peor": None, "estado": None})
            continue
        peor = min(f["criterio"] for f in fs)
        out.append({**r, "filas": len(fs),
                    "promedio": round(sum(f["criterio"] for f in fs) / len(fs), 2),
                    "peor": peor, "estado": estado(peor)})
    return out


def por_control(filas: list[dict]) -> list[dict]:
    """Un renglon por control ISO con su peor criterio."""
    d: dict[str, list[int]] = {}
    for f in filas:
        d.setdefault(f["control"], []).append(f["criterio"])
    def clave(c: str):  # A5.12 -> (5, 12)
        a, b = c[1:].split(".")
        return int(a), int(b)

    return [{"control": c, "peor": min(v), "estado": estado(min(v)), "filas": len(v)}
            for c, v in sorted(d.items(), key=lambda kv: clave(kv[0]))]


def comparar_en_vivo(filas: list[dict], vivo: list[dict]) -> list[dict]:
    """Cruza la matriz de evidencia con la salida del script 08 ejecutado en vivo.

    `vivo` = [{ctl, evidencia, criterio}]. Cada fila de la matriz trae `live`
    (lista de claves ctl + inicio de la evidencia); si hay varias, se toma el
    peor criterio, igual que se anoto en el informe para T-04.
    """
    res = []
    for f in filas:
        if not f.get("live"):
            res.append({"n": f["n"], "tarea": f["tarea"], "control": f["control"],
                        "evidencia": f["criterio"], "vivo": None, "cambio": "manual"})
            continue
        vals = []
        for k in f["live"]:
            m = [v["criterio"] for v in vivo
                 if v["ctl"] == k["ctl"] and v["evidencia"].lower().startswith(k["desde"].lower())]
            vals += m
        if not vals:
            res.append({"n": f["n"], "tarea": f["tarea"], "control": f["control"],
                        "evidencia": f["criterio"], "vivo": None, "cambio": "sin dato"})
            continue
        v = min(vals)
        cambio = "igual" if v == f["criterio"] else ("mejoro" if v > f["criterio"] else "empeoro")
        res.append({"n": f["n"], "tarea": f["tarea"], "control": f["control"],
                    "evidencia": f["criterio"], "vivo": v, "cambio": cambio})
    return res
