"""Pruebas del panel. Ejecutar:  python -m pytest -q   (desde la carpeta panel/)"""
import pytest
from fastapi.testclient import TestClient

from app import config, live, scoring, store
from app.main import app

client = TestClient(app)


# ---- reglas puras ---------------------------------------------------------
@pytest.mark.parametrize("c,e", [(0, "No cumple"), (1, "No cumple"), (2, "Parcial"), (3, "Parcial"), (4, "Cumple")])
def test_estado(c, e):
    assert scoring.estado(c) == e


@pytest.mark.parametrize("c", [-1, 5])
def test_estado_fuera_de_rango(c):
    with pytest.raises(ValueError):
        scoring.estado(c)


@pytest.mark.parametrize("i,p,n", [(5, 4, "Alto"), (5, 3, "Alto"), (4, 3, "Medio"), (1, 6, "Bajo")])
def test_nivel_riesgo(i, p, n):
    assert scoring.nivel_riesgo(i, p) == n


# ---- coherencia de los datos con el informe ---------------------------------
def test_matriz_coincide_con_informe():
    r = scoring.resumen(store.cargar("matriz"))
    assert r["total"] == 16
    assert (r["Cumple"], r["Parcial"], r["No cumple"]) == (4, 7, 5)


def test_niveles_de_riesgo_coinciden_con_calculo():
    for r in store.cargar("riesgos"):
        assert r["valor"] == r["impacto"] * r["probabilidad"]
        assert r["nivel"] == scoring.nivel_riesgo(r["impacto"], r["probabilidad"])


def test_cada_fila_apunta_a_riesgo_y_tarea_existentes():
    riesgos = {r["id"] for r in store.cargar("riesgos")}
    tareas = {t["id"] for t in store.cargar("tareas")}
    for f in store.cargar("matriz"):
        assert f["riesgo"] in riesgos and f["tarea"] in tareas


def test_toda_evidencia_citada_existe_en_la_carpeta():
    existentes = {e["nombre"] for e in store.listar_evidencias()}
    citadas = {l for f in store.cargar("matriz") for l in f["logs"]}
    citadas |= {l for p in store.cargar("pruebas") for l in p["logs"]}
    assert citadas <= existentes, citadas - existentes


# ---- API ----------------------------------------------------------------------
def test_api_resumen_y_matriz():
    assert client.get("/api/resumen").json()["matriz"]["total"] == 16
    m = client.get("/api/matriz").json()
    assert m[0]["estado"] in scoring.ESTADOS


def test_api_colecciones():
    for c in ("riesgos", "tareas", "controles", "observables", "pruebas", "hallazgos"):
        assert client.get(f"/api/{c}").status_code == 200
    assert client.get("/api/secretos").status_code == 404


def test_evidencias_bloquea_path_traversal():
    assert client.get("/api/evidencias/..%2F..%2Fpanel%2F.env").status_code in (400, 404)
    assert client.get("/api/evidencias/archivo.exe").status_code == 400
    assert client.get("/api/evidencias/08_matriz_evaluacion.log").status_code == 200


def test_en_vivo_deshabilitado_sin_credenciales(monkeypatch):
    monkeypatch.setattr(config, "LIVE_ENABLED", False)
    assert client.post("/api/en-vivo/ejecutar").status_code == 503


# ---- modo en vivo: la sentencia sale del script 08 y es de solo lectura ----------
def test_consulta_08_es_select_sin_escritura():
    sql = live.consulta_08()
    assert sql.upper().startswith("WITH")
    assert not sql.rstrip().endswith(";")
    assert "SPOOL" not in sql.upper()


def test_extraer_rechaza_escritura():
    with pytest.raises(ValueError):
        live.extraer_consulta("WITH r AS (SELECT 1 FROM dual)\nDROP USER x;")


class _Cur:
    def __init__(self): self.q = []
    def execute(self, sql): self.q.append(sql)
    def fetchone(self): return ("CONF_AUDITOR", "XEPDB1")
    def fetchall(self):
        return [("A5.18", "Cuentas abiertas sin uso en 120 dias", 2, "Parcial"),
                ("A8.2", "Cuentas de usuario con privilegios ANY", 4, "Cumple"),
                ("A8.24", "Almacen de llaves TDE abierto", 0, "No cumple")]


class _Con:
    cur = _Cur()
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def cursor(self): return self.cur


def test_en_vivo_con_conexion_simulada(monkeypatch):
    monkeypatch.setattr(config, "LIVE_ENABLED", True)
    monkeypatch.setattr(live, "conectar", lambda: _Con())
    r = client.post("/api/en-vivo/ejecutar")
    assert r.status_code == 200
    j = r.json()
    assert j["usuario"] == "CONF_AUDITOR" and len(j["filas"]) == 3
    cambios = {c["tarea"] + c["control"]: c["cambio"] for c in j["comparacion"]}
    assert cambios["T-01A5.18"] == "igual"
    assert cambios["T-06A8.24"] == "igual"
    assert all(q.strip().upper().startswith(("SELECT", "WITH")) for q in _Con.cur.q)
