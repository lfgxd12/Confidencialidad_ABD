SET LINESIZE 200 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\01_privilegios_roles.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN grantee FORMAT A30
COLUMN owner FORMAT A12
COLUMN username FORMAT A15
COLUMN directory_name FORMAT A28
COLUMN directory_path FORMAT A70
COLUMN privilege FORMAT A35
COLUMN granted_role FORMAT A30
COLUMN table_name FORMAT A25
PROMPT === OBS-01 Privilegios ANY en cuentas no mantenidas por Oracle
SELECT s.grantee, s.privilege, s.admin_option, s.inherited
  FROM dba_sys_privs s
  JOIN dba_users u ON u.username = s.grantee
 WHERE s.privilege LIKE '%ANY%' AND u.oracle_maintained = 'N'
 ORDER BY s.grantee, s.privilege;
PROMPT === OBS-02 Cuentas de usuario con el rol DBA
SELECT r.grantee, r.admin_option, r.inherited
  FROM dba_role_privs r
  JOIN dba_users u ON u.username = r.grantee
 WHERE r.granted_role = 'DBA' AND u.oracle_maintained = 'N';
PROMPT === OBS-03 Roles otorgados con ADMIN OPTION o heredados
SELECT grantee, granted_role, admin_option, inherited
  FROM dba_role_privs
 WHERE (admin_option = 'YES' OR inherited = 'YES')
   AND grantee IN (SELECT username FROM dba_users WHERE oracle_maintained = 'N');
PROMPT === OBS-04 Usuarios con privilegios administrativos (archivo de contrasenas)
SELECT username, sysdba, sysoper, sysbackup, sysdg, syskm FROM v$pwfile_users;
PROMPT === OBS-05 Privilegios sobre paquetes de salida de datos otorgados a PUBLIC
SELECT grantee, owner, table_name, privilege
  FROM dba_tab_privs
 WHERE grantee = 'PUBLIC' AND privilege = 'EXECUTE'
   AND table_name IN ('UTL_FILE','UTL_HTTP','UTL_TCP','UTL_SMTP','UTL_INADDR','DBMS_LDAP');
PROMPT === OBS-06 Directorios y roles de exportacion
SELECT owner, directory_name, directory_path FROM dba_directories;
SELECT grantee, granted_role FROM dba_role_privs
 WHERE granted_role IN ('DATAPUMP_EXP_FULL_DATABASE','DATAPUMP_IMP_FULL_DATABASE','EXP_FULL_DATABASE');
SPOOL OFF
