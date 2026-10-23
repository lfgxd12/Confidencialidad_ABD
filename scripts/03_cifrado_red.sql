SET LINESIZE 200 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\03_cifrado_red.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
COLUMN wrl_type FORMAT A12
COLUMN wrl_parameter FORMAT A50
COLUMN tablespace_name FORMAT A25
COLUMN network_service_banner FORMAT A80
PROMPT === OBS-10 Estado del almacen de llaves (wallet)
SELECT wrl_type, wrl_parameter, status, wallet_type FROM v$encryption_wallet;
PROMPT === Columnas y tablespaces cifrados
SELECT owner, table_name, column_name, encryption_alg FROM dba_encrypted_columns;
SELECT tablespace_name, encrypted FROM dba_tablespaces;
SELECT * FROM v$encrypted_tablespaces;
PROMPT === OBS-11 Servicios de red de la sesion actual (busque Encryption service adapter o TCPS)
SELECT DISTINCT network_service_banner FROM v$session_connect_info
 WHERE sid = SYS_CONTEXT('USERENV','SID');
PROMPT === Listener
SELECT name, value FROM v$parameter WHERE name IN ('local_listener','remote_listener','dispatchers');
PROMPT Ejecute en CMD fuera de SQL Developer: lsnrctl status
SPOOL OFF
