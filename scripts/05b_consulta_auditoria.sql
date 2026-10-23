SET LINESIZE 220 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\05b_consulta_auditoria.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN dbusername FORMAT A15
COLUMN action_name FORMAT A18
COLUMN object_name FORMAT A22
COLUMN unified_audit_policies FORMAT A35
EXEC DBMS_AUDIT_MGMT.FLUSH_UNIFIED_AUDIT_TRAIL;
PROMPT === OBS-15 Registros de la pista de auditoria sobre objetos confidenciales
SELECT event_timestamp, dbusername, action_name, object_name, return_code, unified_audit_policies
  FROM unified_audit_trail
 WHERE object_schema = 'CONF_DEMO' OR unified_audit_policies LIKE '%POL_CONF%'
 ORDER BY event_timestamp DESC FETCH FIRST 30 ROWS ONLY;
PROMPT === Retencion y parametros de gestion de la pista
SELECT audit_trail, parameter_name, parameter_value FROM dba_audit_mgmt_config_params;
SPOOL OFF
