SET LINESIZE 220 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\08_matriz_evaluacion.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN ctl FORMAT A8
COLUMN evidencia FORMAT A70
COLUMN estado FORMAT A12
WITH r AS (
  SELECT 'A8.2' ctl, 'Cuentas de usuario con privilegios ANY' evidencia,
         CASE WHEN n = 0 THEN 4 WHEN n <= 2 THEN 3 WHEN n <= 5 THEN 2 ELSE 0 END crit
    FROM (SELECT COUNT(DISTINCT s.grantee) n FROM dba_sys_privs s
            JOIN dba_users u ON u.username = s.grantee
           WHERE s.privilege LIKE '%ANY%' AND u.oracle_maintained = 'N')
  UNION ALL
  SELECT 'A8.2', 'Cuentas de usuario con el rol DBA',
         CASE WHEN n = 0 THEN 4 WHEN n = 1 THEN 3 WHEN n = 2 THEN 2 ELSE 0 END
    FROM (SELECT COUNT(*) n FROM dba_role_privs r JOIN dba_users u ON u.username = r.grantee
           WHERE r.granted_role = 'DBA' AND u.oracle_maintained = 'N')
  UNION ALL
  SELECT 'A8.12', 'PUBLIC con EXECUTE sobre paquetes UTL_*',
         CASE WHEN n = 0 THEN 4 WHEN n <= 2 THEN 2 ELSE 1 END
    FROM (SELECT COUNT(*) n FROM dba_tab_privs
           WHERE grantee = 'PUBLIC' AND privilege = 'EXECUTE'
             AND table_name IN ('UTL_FILE','UTL_HTTP','UTL_TCP','UTL_SMTP'))
  UNION ALL
  SELECT 'A5.17', 'Cuentas con contrasena por defecto (CIS 4.1)',
         CASE WHEN n = 0 THEN 4 WHEN n <= 3 THEN 2 ELSE 0 END
    FROM (SELECT COUNT(*) n FROM dba_users_with_defpwd)
  UNION ALL
  SELECT 'A8.5', 'FAILED_LOGIN_ATTEMPTS del perfil DEFAULT (CIS 3.1: 5 o menos)',
         CASE WHEN l = 'UNLIMITED' THEN 0
              WHEN REGEXP_LIKE(l, '^[0-9]+$') AND TO_NUMBER(l) <= 5 THEN 4
              WHEN REGEXP_LIKE(l, '^[0-9]+$') AND TO_NUMBER(l) <= 10 THEN 2
              ELSE 1 END
    FROM (SELECT MAX(limit) l FROM dba_profiles
           WHERE profile = 'DEFAULT' AND resource_name = 'FAILED_LOGIN_ATTEMPTS')
  UNION ALL
  SELECT 'A5.17', 'PASSWORD_LIFE_TIME del perfil DEFAULT (CIS 3.3: 90 o menos)',
         CASE WHEN l = 'UNLIMITED' THEN 0
              WHEN REGEXP_LIKE(l, '^[0-9.]+$') AND TO_NUMBER(l) <= 90 THEN 4
              ELSE 2 END
    FROM (SELECT MAX(limit) l FROM dba_profiles
           WHERE profile = 'DEFAULT' AND resource_name = 'PASSWORD_LIFE_TIME')
  UNION ALL
  SELECT 'A5.17', 'PASSWORD_LOCK_TIME del perfil DEFAULT (CIS 3.2: 1 o mas)',
         CASE WHEN l = 'UNLIMITED' THEN 4
              WHEN REGEXP_LIKE(l, '^[0-9.]+$') AND TO_NUMBER(l) >= 1 THEN 4
              ELSE 2 END
    FROM (SELECT MAX(limit) l FROM dba_profiles
           WHERE profile = 'DEFAULT' AND resource_name = 'PASSWORD_LOCK_TIME')
  UNION ALL
  SELECT 'A5.18', 'INACTIVE_ACCOUNT_TIME del perfil DEFAULT (CIS 3.9: 120 o menos)',
         CASE WHEN l = 'UNLIMITED' THEN 0
              WHEN REGEXP_LIKE(l, '^[0-9]+$') AND TO_NUMBER(l) <= 120 THEN 4
              ELSE 2 END
    FROM (SELECT MAX(limit) l FROM dba_profiles
           WHERE profile = 'DEFAULT' AND resource_name = 'INACTIVE_ACCOUNT_TIME')
  UNION ALL
  SELECT 'A5.17', 'PASSWORD_VERIFY_FUNCTION del perfil DEFAULT (CIS 3.7)',
         CASE WHEN l = 'NULL' THEN 0 ELSE 4 END
    FROM (SELECT MAX(limit) l FROM dba_profiles
           WHERE profile = 'DEFAULT' AND resource_name = 'PASSWORD_VERIFY_FUNCTION')
  UNION ALL
  SELECT 'A5.18', 'Cuentas abiertas sin uso en 120 dias',
         CASE WHEN n = 0 THEN 4 WHEN n <= 2 THEN 2 ELSE 0 END
    FROM (SELECT COUNT(*) n FROM dba_users
           WHERE oracle_maintained = 'N' AND account_status = 'OPEN'
             AND (last_login IS NULL OR last_login < SYSTIMESTAMP - INTERVAL '120' DAY(3)))
  UNION ALL
  SELECT 'A8.24', 'Almacen de llaves TDE abierto',
         CASE WHEN n > 0 THEN 4 ELSE 0 END
    FROM (SELECT COUNT(*) n FROM v$encryption_wallet WHERE status = 'OPEN')
  UNION ALL
  SELECT 'A8.15', 'Politicas de auditoria unificada habilitadas',
         CASE WHEN n = 0 THEN 0 WHEN n <= 2 THEN 2 ELSE 4 END
    FROM (SELECT COUNT(DISTINCT policy_name) n FROM audit_unified_enabled_policies)
  UNION ALL
  SELECT 'A8.13', 'ARCHIVELOG activo (respaldo y cifrado se evaluan con RMAN, 06b)',
         CASE WHEN m = 'ARCHIVELOG' THEN 2 ELSE 0 END
    FROM (SELECT log_mode m FROM v$database)
  UNION ALL
  SELECT 'A8.20', 'Sesiones con adaptador de cifrado de red activo',
         CASE WHEN n > 0 THEN 4 ELSE 1 END
    FROM (SELECT COUNT(*) n FROM v$session_connect_info
           WHERE network_service_banner LIKE '%Encryption service adapter%' OR network_service_banner LIKE '%TCPS%')
  UNION ALL
  SELECT 'A8.8', 'Parche SQL exitoso en los ultimos 365 dias',
         CASE WHEN n > 0 THEN 4 ELSE 1 END
    FROM (SELECT COUNT(*) n FROM dba_registry_sqlpatch
           WHERE status = 'SUCCESS' AND action_time > SYSTIMESTAMP - INTERVAL '365' DAY(3))
)
SELECT ctl, evidencia, crit AS criterio,
       CASE WHEN crit = 4 THEN 'Cumple' WHEN crit >= 2 THEN 'Parcial' ELSE 'No cumple' END estado
  FROM r ORDER BY ctl;
SPOOL OFF
