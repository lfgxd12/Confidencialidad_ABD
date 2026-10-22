SET LINESIZE 220 PAGESIZE 100 FEEDBACK ON
SPOOL 06_respaldos_logs_parcheo.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN name FORMAT A60
COLUMN input_type FORMAT A15
COLUMN status FORMAT A25
COLUMN value FORMAT A70
PROMPT === Modo de archivado y redo
SELECT log_mode, force_logging FROM v$database;
SELECT group#, status, archived FROM v$log;
SELECT name, completion_time FROM v$archived_log ORDER BY completion_time DESC FETCH FIRST 10 ROWS ONLY;
PROMPT === Respaldos RMAN recientes
SELECT input_type, status, TO_CHAR(start_time,'YYYY-MM-DD HH24:MI') inicio, output_bytes_display
  FROM v$rman_backup_job_details ORDER BY start_time DESC FETCH FIRST 10 ROWS ONLY;
PROMPT === Quien puede minar el redo (LogMiner)
SELECT grantee, privilege FROM dba_sys_privs WHERE privilege = 'LOGMINING';
SELECT grantee, granted_role FROM dba_role_privs WHERE granted_role IN ('EXECUTE_CATALOG_ROLE','LOGMINING');
PROMPT === Ubicacion de alert log y trazas
SELECT name, value FROM v$diag_info WHERE name IN ('Diag Trace','Diag Alert','ADR Home');
PROMPT === Version y parches aplicados
SELECT banner_full FROM v$version;
SELECT patch_id, action, status, action_time FROM dba_registry_sqlpatch ORDER BY action_time DESC;
PROMPT === Eliminacion segura: papelera de reciclaje
SELECT value FROM v$parameter WHERE name = 'recyclebin';
SELECT owner, COUNT(*) objetos_en_papelera FROM dba_recyclebin GROUP BY owner;
PROMPT Para respaldos cifrados ejecute en RMAN: SHOW ALL;
SPOOL OFF
