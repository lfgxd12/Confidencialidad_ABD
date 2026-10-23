SET LINESIZE 220 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\05d_prueba_privilegiados.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN dbusername FORMAT A15
COLUMN action_name FORMAT A18
COLUMN object_name FORMAT A22
COLUMN unified_audit_policies FORMAT A35
CREATE USER conf_prueba IDENTIFIED BY "Conf_Prueba#2026";
GRANT CREATE SESSION TO conf_prueba;
DROP USER conf_prueba;
EXEC DBMS_AUDIT_MGMT.FLUSH_UNIFIED_AUDIT_TRAIL;
PROMPT === PT-07 Eventos de la politica de acciones privilegiadas
SELECT event_timestamp, dbusername, action_name, object_name, return_code, unified_audit_policies
  FROM unified_audit_trail
 WHERE unified_audit_policies LIKE '%POL_CONF_PRIVILEGIADOS%'
 ORDER BY event_timestamp DESC FETCH FIRST 20 ROWS ONLY;
SPOOL OFF
