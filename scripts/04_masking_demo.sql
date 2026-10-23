SET LINESIZE 200 PAGESIZE 100 FEEDBACK ON
SPOOL C:\Users\lfgxd\Desktop\Confidencialidad_ABD_119130110\evidencias\04_masking_demo.log
SELECT USER AS usuario, SYS_CONTEXT('USERENV','CON_NAME') AS contenedor, TO_CHAR(SYSTIMESTAMP,'YYYY-MM-DD HH24:MI:SS TZR') AS fecha FROM dual;
PROMPT Conectado como SYS al PDB (XEPDB1). Crea el esquema demo de clasificacion y masking.
CREATE USER conf_demo IDENTIFIED BY "Conf_Demo#2026" DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW TO conf_demo;

CREATE TABLE conf_demo.clientes (
  id        NUMBER PRIMARY KEY,
  nombre    VARCHAR2(60),
  cedula    VARCHAR2(12),
  tarjeta   VARCHAR2(19),
  salario   NUMBER(12,2)
);
INSERT INTO conf_demo.clientes VALUES (1,'Ana Mora','1-0456-0789','4111-2222-3333-4444',850000);
INSERT INTO conf_demo.clientes VALUES (2,'Luis Rojas','2-0555-0123','5500-1111-2222-3333',1200000);
INSERT INTO conf_demo.clientes VALUES (3,'Sara Vega','3-0321-0654','4000-9999-8888-7777',640000);
COMMIT;

COMMENT ON COLUMN conf_demo.clientes.cedula  IS 'CLASIF=CONFIDENCIAL;Ley8968=dato personal';
COMMENT ON COLUMN conf_demo.clientes.tarjeta IS 'CLASIF=RESTRINGIDO;PCI';
COMMENT ON COLUMN conf_demo.clientes.salario IS 'CLASIF=CONFIDENCIAL';

CREATE OR REPLACE VIEW conf_demo.v_clientes_mask AS
SELECT id, nombre,
       SUBSTR(cedula,1,1) || '-XXXX-XXXX' AS cedula,
       'XXXX-XXXX-XXXX-' || SUBSTR(tarjeta,-4) AS tarjeta
  FROM conf_demo.clientes;

CREATE ROLE rol_consulta_mask;
GRANT SELECT ON conf_demo.v_clientes_mask TO rol_consulta_mask;
CREATE USER conf_analista IDENTIFIED BY "Conf_Analista#2026";
GRANT CREATE SESSION TO conf_analista;
GRANT rol_consulta_mask TO conf_analista;

PROMPT === OBS-12 Columnas clasificadas
SELECT owner, table_name, column_name, comments FROM dba_col_comments
 WHERE comments LIKE 'CLASIF=%';
PROMPT === OBS-13 Privilegios efectivos del analista
SELECT grantee, owner, table_name, privilege FROM dba_tab_privs WHERE grantee = 'ROL_CONSULTA_MASK';
SELECT grantee, granted_role FROM dba_role_privs WHERE grantee = 'CONF_ANALISTA';
PROMPT === Politicas de Data Redaction si la edicion las soporta
SELECT object_owner, object_name, policy_name, enable FROM redaction_policies;
SPOOL OFF
