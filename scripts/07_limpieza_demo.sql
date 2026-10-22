SET FEEDBACK ON
SPOOL 07_limpieza_demo.log
NOAUDIT POLICY pol_conf_clientes;
DROP AUDIT POLICY pol_conf_clientes;
NOAUDIT POLICY pol_conf_privilegiados;
DROP AUDIT POLICY pol_conf_privilegiados;
DROP USER conf_analista;
DROP ROLE rol_consulta_mask;
DROP USER conf_demo CASCADE;
DROP USER conf_auditor;
SELECT username FROM dba_users WHERE username LIKE 'CONF%';
SPOOL OFF
