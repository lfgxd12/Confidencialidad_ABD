SET LINESIZE 200 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\00_crear_auditor.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
CREATE USER conf_auditor IDENTIFIED BY "Conf_Auditor#2026";
GRANT CREATE SESSION, SELECT_CATALOG_ROLE, AUDIT_VIEWER TO conf_auditor;
SELECT grantee, granted_role FROM dba_role_privs WHERE grantee = 'CONF_AUDITOR';
SELECT grantee, privilege FROM dba_sys_privs WHERE grantee = 'CONF_AUDITOR';
SPOOL OFF
