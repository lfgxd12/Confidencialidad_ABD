"""Pruebas del laboratorio con una conexion simulada (no toca Oracle)."""
import pytest
from fastapi.testclient import TestClient

from app import config, lab
from app.main import app

client = TestClient(app)


def _sql(items):
    return [i["texto"] for i in items if i["tipo"] == "sql"]


def test_todos_los_scripts_se_analizan():
    for id_, m in lab.LAB_SCRIPTS.items():
        items = lab.analizar((config.SCRIPTS_DIR / m["file"]).read_text(encoding="utf-8"))
        assert any(i["tipo"] == "sql" for i in items), id_


def test_script_04_sentencias():
    s = _sql(lab.analizar((config.SCRIPTS_DIR / "04_masking_demo.sql").read_text(encoding="utf-8")))
    assert s[0].startswith("SELECT USER")  # cabecera
    assert sum(x.upper().startswith("CREATE USER") for x in s) == 2
    assert sum(x.upper().startswith("INSERT") for x in s) == 3
    assert "COMMIT" in [x.upper() for x in s]
    assert not any("SPOOL" in x.upper() or x.upper().startswith("PROMPT") for x in s)


def test_07_contiene_los_drops_esperados():
    s = [x.upper() for x in _sql(lab.analizar((config.SCRIPTS_DIR / "07_limpieza_demo.sql").read_text(encoding="utf-8")))]
    assert "DROP USER CONF_DEMO CASCADE" in s and "DROP USER CONF_AUDITOR" in s


def test_exec_se_convierte_en_bloque():
    it = lab.analizar("EXEC DBMS_AUDIT_MGMT.FLUSH_UNIFIED_AUDIT_TRAIL;\n")
    assert it == [{"tipo": "exec", "texto": "BEGIN DBMS_AUDIT_MGMT.FLUSH_UNIFIED_AUDIT_TRAIL; END;"}]


def test_punto_y_coma_dentro_de_comillas_y_comentarios():
    s = _sql(lab.analizar("-- a; b\nSELECT 'x;y' FROM dual; /* c; d */ SELECT 2 FROM dual;"))
    assert s == ["SELECT 'x;y' FROM dual", "SELECT 2 FROM dual"]


def test_rechaza_plsql():
    with pytest.raises(ValueError):
        lab.analizar("BEGIN\n null;\nEND;\n/")


class Cur:
    def __init__(self, con_name="XEPDB1"):
        self.con_name, self.q, self.description, self.rowcount, self._r = con_name, [], None, -1, []

    def execute(self, sql):
        self.q.append(sql)
        if "FROM dual" in sql and "CON_NAME" in sql:
            self.description, self._r = [("U",), ("C",)], [("SYS", self.con_name)]
        elif sql.upper().startswith("SELECT"):
            self.description, self._r = [("A",)], [("1",)]
        elif "FALLA" in sql.upper() or "DROP USER CONF_AUDITOR" in sql.upper():
            raise Exception("ORA-01918: el usuario no existe")
        else:
            self.description, self.rowcount = None, -1

    def fetchone(self): return self._r[0]
    def fetchall(self): return self._r


class Con:
    def __init__(self, cur): self.cur, self.commits = cur, 0
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def cursor(self): return self.cur
    def commit(self): self.commits += 1


@pytest.fixture
def lab_on(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "LAB_ENABLED", True)
    monkeypatch.setattr(config, "SYS_PASSWORD", "x")
    monkeypatch.setattr(lab, "LAB_DIR_LOGS", tmp_path)
    return tmp_path


def test_ejecutar_guarda_log_y_continua_tras_error(lab_on):
    cur = Cur()
    r = lab.ejecutar("07", conectar_fn=lambda como: Con(cur))
    assert r["errores"] == 1 and "ORA-01918" in r["salida"]
    assert any(q.upper().startswith("DROP USER CONF_DEMO") for q in cur.q)  # siguio despues del error
    assert (lab_on / r["log"].split("/")[1]).exists()


def test_rechaza_contenedor_equivocado(lab_on):
    with pytest.raises(RuntimeError, match="CDB"):
        lab.ejecutar("04", conectar_fn=lambda como: Con(Cur("CDB$ROOT")))


def test_apagado_por_defecto(monkeypatch):
    monkeypatch.setattr(config, "LAB_ENABLED", False)
    assert client.post("/api/lab/ejecutar/04", json={"confirmacion": "EJECUTAR 04"}).status_code == 503


def test_exige_confirmacion_exacta(lab_on):
    assert client.post("/api/lab/ejecutar/07", json={"confirmacion": "ejecutar"}).status_code == 400
    assert client.post("/api/lab/ejecutar/07", json={"confirmacion": "EJECUTAR 04"}).status_code == 400


def test_script_fuera_de_lista_blanca(lab_on):
    assert client.post("/api/lab/ejecutar/99", json={"confirmacion": "EJECUTAR 99"}).status_code == 404
    assert client.get("/api/lab/vista-previa/..%2Fx").status_code == 404


def test_vista_previa_no_conecta():
    j = client.get("/api/lab/vista-previa/07").json()
    assert j["como"] == "sys" and len(j["items"]) >= 8


def test_host_ajeno_bloqueado():
    assert client.get("/api/estado", headers={"host": "evil.com"}).status_code == 403
    assert client.get("/api/estado", headers={"host": "localhost:8000"}).status_code == 200


def test_endpoint_ejecuta_y_responde(lab_on, monkeypatch):
    monkeypatch.setattr(lab, "conectar", lambda como: Con(Cur()))
    r = client.post("/api/lab/ejecutar/05d", json={"confirmacion": "EJECUTAR 05d"})
    assert r.status_code == 200 and r.json()["contenedor"] == "XEPDB1"
