SET LINESIZE 200 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\00b_ajuste_auditor.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
GRANT SELECT ON sys.dba_users_with_defpwd TO conf_auditor;
SELECT grantee, owner, table_name, privilege FROM dba_tab_privs WHERE grantee = 'CONF_AUDITOR';
SPOOL OFF
