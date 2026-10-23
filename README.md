# Controles ISO/IEC 27001:2022 para la confidencialidad en la administración de bases de datos Oracle

Asignación individual de Administración de Bases de Datos, II Ciclo 2026.
Universidad Nacional de Costa Rica, Escuela de Informática. Prof. Johnny Villalobos Murillo.
Estudiante: Luis Felipe Jiménez Fernández.

## Contenido

| Carpeta | Qué contiene |
|---|---|
| `informe/` | Informe en PDF con riesgos R-CONF, tareas del DBA, mapeo de controles, matriz y pruebas |
| `scripts/` | Scripts SQL de verificación y demostración (00 a 08) |
| `evidencias/` | Salidas `.log` de cada script, capturas y la matriz de evaluación completada |
| `ia/` | Tabla de uso de inteligencia artificial y declaración jurada firmada |

## Entorno

Oracle Database 21c XE (multitenant, PDB `XEPDB1`), Oracle SQL Developer.

## Orden de ejecución

| Paso | Script | Usuario | Tipo |
|---|---|---|---|
| 1 | `00_crear_auditor.sql` | SYS | Crea el usuario auditor de solo lectura |
| 1b | `00b_ajuste_auditor.sql` | SYS | Concede al auditor la vista de contraseñas por defecto |
| 2 | `01_privilegios_roles.sql` | `conf_auditor` | Lectura |
| 3 | `02_autenticacion_perfiles.sql` | `conf_auditor` | Lectura |
| 4 | `03_cifrado_red.sql` | `conf_auditor` | Lectura |
| 5 | `06_respaldos_logs_parcheo.sql` | `conf_auditor` | Lectura |
| 6 | `04_masking_demo.sql` | SYS | Crea el esquema de demostración |
| 7 | `05a_politicas_auditoria.sql` | SYS | Crea políticas de auditoría |
| 8 | Consultas manuales indicadas en el 05a | `conf_analista` | Genera eventos auditables |
| 9 | `05b_consulta_auditoria.sql` | SYS | Consulta la pista de auditoría |
| 10 | `08_matriz_evaluacion.sql` | `conf_auditor` | Calcula criterio y estado |
| 11 | `07_limpieza_demo.sql` | SYS | Elimina los usuarios y políticas de demostración |

Cada script genera un archivo `.log` con `SPOOL`; se guarda en `evidencias/`.
El `lsnrctl status` del script 03 se ejecuta aparte en CMD.

## Nota de seguridad

Las contraseñas de `conf_demo`, `conf_analista` y `conf_auditor` son de laboratorio y deben eliminarse con el script 07. No usar en ambientes reales.

## Uso de inteligencia artificial

Se utilizó Claude (Anthropic) como apoyo. El detalle, la validación y la declaración están en `ia/`.

## Entregables

Informe PDF, scripts SQL, este repositorio, video de 5 minutos y tabla de uso de IA firmada.
