SET LINESIZE 200 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\02_autenticacion_perfiles.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN username FORMAT A25
COLUMN profile FORMAT A20
COLUMN resource_name FORMAT A30
COLUMN limit FORMAT A30
COLUMN name FORMAT A35
COLUMN value FORMAT A30
PROMPT === OBS-07 Cuentas con contrasena por defecto
SELECT username, product FROM dba_users_with_defpwd ORDER BY username;
PROMPT === OBS-08 Politica de contrasenas por perfil
SELECT profile, resource_name, limit FROM dba_profiles
 WHERE resource_name IN ('FAILED_LOGIN_ATTEMPTS','PASSWORD_LIFE_TIME','PASSWORD_REUSE_MAX',
                         'PASSWORD_LOCK_TIME','PASSWORD_VERIFY_FUNCTION','INACTIVE_ACCOUNT_TIME')
 ORDER BY profile, resource_name;
PROMPT === OBS-09 Cuentas abiertas de usuario sin uso en 120 dias o sin ingreso registrado
SELECT username, account_status, profile, last_login
  FROM dba_users
 WHERE oracle_maintained = 'N' AND account_status = 'OPEN'
   AND (last_login IS NULL OR last_login < SYSTIMESTAMP - INTERVAL '120' DAY(3));
PROMPT === Parametros de autenticacion
SELECT name, value FROM v$parameter
 WHERE name IN ('remote_login_passwordfile','sec_max_failed_login_attempts',
                'sec_protocol_error_further_action','o7_dictionary_accessibility');
SPOOL OFF
