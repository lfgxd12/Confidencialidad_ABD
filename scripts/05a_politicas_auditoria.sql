SET LINESIZE 220 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\05a_politicas_auditoria.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN dbusername FORMAT A15
COLUMN action_name FORMAT A18
COLUMN object_name FORMAT A22
COLUMN unified_audit_policies FORMAT A35
COLUMN policy_name FORMAT A30
PROMPT === OBS-14 Auditoria unificada habilitada
SELECT parameter, value FROM v$option WHERE parameter = 'Unified Auditing';
SELECT policy_name, enabled_option, entity_name, success, failure FROM audit_unified_enabled_policies;

CREATE AUDIT POLICY pol_conf_clientes
  ACTIONS SELECT ON conf_demo.clientes, UPDATE ON conf_demo.clientes,
          SELECT ON conf_demo.v_clientes_mask;
AUDIT POLICY pol_conf_clientes;
CREATE AUDIT POLICY pol_conf_privilegiados
  ACTIONS CREATE USER, ALTER USER, DROP USER, GRANT, REVOKE, CREATE ROLE;
AUDIT POLICY pol_conf_privilegiados;
PROMPT Politicas creadas. Ahora, desde otra hoja conectada como CONF_ANALISTA, ejecute:
PROMPT SELECT * FROM conf_demo.v_clientes_mask;
PROMPT SELECT * FROM conf_demo.clientes;
PROMPT Luego ejecute 05b_consulta_auditoria.sql como SYS.
SPOOL OFF
