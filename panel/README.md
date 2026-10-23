# Panel de controles ISO 27001 (confidencialidad del DBA)

Panel web local para **ver** los resultados de la evaluación (matriz 0-4, riesgos, pruebas, hallazgos, logs de evidencia) y para **verificar en vivo, solo lectura**, el estado de una base Oracle 21c XE con el mismo criterio del script `scripts/08_matriz_evaluacion.sql`.

Python 3.10+ y FastAPI. Escucha solo en `127.0.0.1`.

## Cómo abrirlo (modo evidencia, sin Oracle)

Windows: doble clic en `panel/run.bat`. Linux/macOS: `panel/run.sh`.
Luego abrir http://127.0.0.1:8000 . La documentación automática de la API está en http://127.0.0.1:8000/docs

Manual:
```bash
cd panel
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Pruebas automáticas
```bash
cd panel
python -m pytest -q        # 36 pruebas: reglas 0-4, coherencia con el informe, API, seguridad, laboratorio
```
Verifican, entre otras cosas, que la matriz del panel coincide con el informe (4 Cumple, 7 Parcial, 5 No cumple sobre 16 filas), que cada log citado existe y que no se puede leer fuera de `evidencias/`.

## Modo en vivo (opcional, lectura)
1. En el PDB `XEPDB1`, como SYS, ejecutar `scripts/00_crear_auditor.sql` y `scripts/00b_ajuste_auditor.sql` (crean `conf_auditor` solo con lectura de catálogo; el script 07 lo elimina al limpiar).
2. Copiar `.env.example` a `.env` y poner la contraseña de `conf_auditor`. `.env` está en `.gitignore`.
3. Reiniciar el panel, pestaña **En vivo**, botón **Ejecutar verificación**.

El panel ejecuta **una sola sentencia**, extraída del propio script 08 (no hay SQL duplicado ni endpoint que reciba SQL del navegador). Las credenciales viven solo en el servidor.

### Cómo leer las diferencias contra el informe
- El script 07 borró las políticas de auditoría de la demostración, por lo que **T-09 baja** de 4 a la línea base.
- **A8.20** mide la sesión del propio panel (driver Python), no la de SQL Developer.
- Las filas **manuales** (T-05, T-07, T-10, T-13) no se calculan en vivo.
- El informe habla de 15 criterios del script 08 (5/5/5); la matriz del informe tiene 16 filas porque T-04 aparece en tres controles y otras filas son manuales.

## Laboratorio (escribe en la base; apagado por defecto)
Pestaña **Laboratorio**: ejecuta desde la web los scripts del repositorio, incluidos los que modifican (00, 00b, 04, 05a, 05b, 05d, 07), con SYS.
1. En `.env`: `LAB_ENABLED=true` y `SYS_PASSWORD=...`; reiniciar el panel.
2. Orden sugerido (la tabla lo muestra): 00, 00b, 04, 05a, 05c, 05b, 05d, lecturas 01/02/03/06/08 y, al final, 07 (limpieza).
3. Cada ejecución pide escribir `EJECUTAR <id>`. Hay **vista previa** de las sentencias sin conectarse.

Salvaguardas: lista blanca de scripts (no hay SQL libre), apagado por defecto, confirmación escrita, se aborta si el contenedor no es `XEPDB1`, un solo script a la vez, el panel solo atiende `Host` local y cada corrida queda en `evidencias/panel/<id>_<fecha>.log` sin sobrescribir los logs originales.
Limitaciones: el analizador entiende solo lo que usan estos scripts (SET, SPOOL, COLUMN, PROMPT, EXEC); no ejecuta bloques PL/SQL con `/`. La salida es una tabla simple, no el formato exacto de SQL Developer. Probado con conexión simulada; la primera ejecución real conviene hacerla con 01 o 08 (lectura) antes de 07.

## Estructura
```
panel/
  app/        config.py · scoring.py (reglas 0-4) · store.py (JSON) · live.py (Oracle, lectura) · lab.py (laboratorio) · main.py (API)
  data/       riesgos, tareas, controles, observables, matriz, pruebas, hallazgos (.json): fuente única
  static/     index.html (interfaz)
  tests/      test_panel.py · test_lab.py
```
Los datos salen del informe y de `evidencias/Matriz_Evaluacion_Completada.xlsx`; si cambia una calificación, se edita `data/matriz.json` y las pruebas avisan si deja de coincidir con el informe.

## Alcance y límites
- El modo en vivo fue probado con una conexión simulada; la ejecución contra Oracle real depende de que el usuario del `.env` tenga los permisos de los scripts 00 y 00b.
- Los scripts que modifican la base solo corren desde la pestaña Laboratorio, si se activa expresamente.
- La regla "estado del riesgo = peor control asociado" es una convención de presentación del panel, no parte de la matriz del informe.
