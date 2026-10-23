SET LINESIZE 200 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\05c_pruebas_analista.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
PROMPT === PT-05 Consulta a la vista enmascarada
SELECT * FROM conf_demo.v_clientes_mask;
PROMPT === PT-04 Consulta directa a la tabla base (debe fallar con ORA-00942)
SELECT * FROM conf_demo.clientes;
SPOOL OFF
