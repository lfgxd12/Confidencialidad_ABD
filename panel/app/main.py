"""API del panel.

Analogia Spring Boot (para quien viene de Java):
  FastAPI()                 ~ @SpringBootApplication
  @app.get("/api/x")        ~ @GetMapping("/api/x") en un @RestController
  Parametros tipados        ~ @PathVariable / @RequestParam (se validan solos por el tipo)
  response_model / Pydantic ~ DTOs con validacion
  Depends(...)              ~ inyeccion de dependencias (@Autowired)
  uvicorn                   ~ el Tomcat embebido
  /docs                     ~ Swagger/OpenAPI, ya viene incluido
"""
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config, lab, live, scoring, store

app = FastAPI(title="Panel de Controles ISO 27001 - Confidencialidad ABD",
              version="1.0", description="Resultados de la evaluacion y verificacion en vivo (solo lectura).")


_HOSTS = ("127.0.0.1", "localhost", "[::1]", "testserver")


@app.middleware("http")
async def solo_local(request: Request, call_next):
    """Defensa contra DNS rebinding: solo se atiende si el Host es local."""
    host = (request.headers.get("host") or "").rsplit(":", 1)[0] if not (request.headers.get("host") or "").startswith("[") else "[::1]"
    if host not in _HOSTS:
        return JSONResponse({"detail": "Host no permitido"}, status_code=403)
    return await call_next(request)


@app.get("/api/estado")
def estado_servicio():
    return {"ok": True, "modo_vivo_disponible": config.LIVE_ENABLED,
            "dsn": config.ORACLE_DSN if config.LIVE_ENABLED else None,
            "lab_disponible": lab.habilitado(),
            "evidencias": len(store.listar_evidencias())}


@app.get("/api/resumen")
def resumen():
    filas = store.cargar("matriz")
    riesgos = store.cargar("riesgos")
    return {"matriz": scoring.resumen(filas),
            "por_riesgo": scoring.por_riesgo(filas, riesgos),
            "por_control": scoring.por_control(filas),
            "hallazgos": {p: sum(1 for h in store.cargar("hallazgos") if h["prioridad"] == p)
                          for p in ("Alta", "Media", "Baja")}}


@app.get("/api/matriz")
def matriz():
    return [{**f, "estado": scoring.estado(f["criterio"])} for f in store.cargar("matriz")]


class Ejecucion(BaseModel):
    confirmacion: str


@app.get("/api/lab/catalogo")
def lab_catalogo():
    return {"habilitado": lab.habilitado(), "contenedor_esperado": config.EXPECTED_CON, "scripts": lab.catalogo()}


@app.get("/api/lab/estado")
def lab_estado():
    try:
        return lab.estado_demo()
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"Fallo al consultar Oracle: {e}")


@app.get("/api/lab/vista-previa/{id_}")
def lab_vista_previa(id_: str):
    """Muestra las sentencias que se ejecutarian, sin conectarse a Oracle."""
    meta = lab.LAB_SCRIPTS.get(id_)
    if not meta:
        raise HTTPException(404, "script no permitido")
    items = lab.analizar((config.SCRIPTS_DIR / meta["file"]).read_text(encoding="utf-8"))
    return {"id": id_, "como": meta["como"], "items": [i for i in items if i["tipo"] != "ignorar"]}


@app.post("/api/lab/ejecutar/{id_}")
def lab_ejecutar(id_: str, cuerpo: Ejecucion):
    if id_ not in lab.LAB_SCRIPTS:
        raise HTTPException(404, "script no permitido")
    if cuerpo.confirmacion.strip() != f"EJECUTAR {id_}":
        raise HTTPException(400, f"Confirmacion incorrecta: escribe exactamente EJECUTAR {id_}")
    try:
        return lab.ejecutar(id_)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(502, f"Fallo al ejecutar en Oracle: {e}")


@app.get("/api/{coleccion}")
def coleccion(coleccion: str):
    if coleccion not in ("riesgos", "tareas", "controles", "observables", "pruebas", "hallazgos"):
        raise HTTPException(404, "coleccion desconocida")
    return store.cargar(coleccion)


@app.get("/api/evidencias/lista")
def evidencias():
    return store.listar_evidencias()


@app.get("/api/evidencias/{nombre}", response_class=PlainTextResponse)
def evidencia(nombre: str):
    try:
        return store.leer_evidencia(nombre)
    except PermissionError:
        raise HTTPException(400, "nombre de evidencia no permitido")
    except FileNotFoundError:
        raise HTTPException(404, "evidencia no encontrada")


@app.post("/api/en-vivo/ejecutar")
def en_vivo():
    """Ejecuta el script 08 contra Oracle (lectura) y lo compara con la evidencia."""
    try:
        r = live.ejecutar()
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:  # error de conexion / permisos de Oracle
        raise HTTPException(502, f"Fallo al consultar Oracle: {e}")
    cmp_ = scoring.comparar_en_vivo(store.cargar("matriz"), r["filas"])
    r["resumen"] = scoring.resumen([{"criterio": f["criterio"]} for f in r["filas"]])
    r["comparacion"] = cmp_
    r["ejecutado"] = datetime.now().astimezone().isoformat(timespec="seconds")
    return r


@app.get("/")
def indice():
    return FileResponse(config.STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
