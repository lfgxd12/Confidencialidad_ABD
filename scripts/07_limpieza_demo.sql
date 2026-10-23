SET FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\07_limpieza_demo.log
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
