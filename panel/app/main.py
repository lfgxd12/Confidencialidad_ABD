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

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config, live, scoring, store

app = FastAPI(title="Panel de Controles ISO 27001 - Confidencialidad ABD",
              version="1.0", description="Resultados de la evaluacion y verificacion en vivo (solo lectura).")


@app.get("/api/estado")
def estado_servicio():
    return {"ok": True, "modo_vivo_disponible": config.LIVE_ENABLED,
            "dsn": config.ORACLE_DSN if config.LIVE_ENABLED else None,
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
