SET LINESIZE 200 FEEDBACK ON
SPOOL 00_crear_auditor.log
CREATE USER conf_auditor IDENTIFIED BY "Conf_Auditor#2026";
GRANT CREATE SESSION, SELECT_CATALOG_ROLE, AUDIT_VIEWER TO conf_auditor;
SELECT grantee, granted_role FROM dba_role_privs WHERE grantee = 'CONF_AUDITOR';
SELECT grantee, privilege FROM dba_sys_privs WHERE grantee = 'CONF_AUDITOR';
SPOOL OFF
