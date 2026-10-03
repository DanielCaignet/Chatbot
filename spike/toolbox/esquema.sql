-- Esquema sintético de tienda para SPEC-001 (V2/V3). Todos los datos son inventados.
-- Requiere PostgreSQL 15 o superior (usa \getenv de psql). Se carga con la imagen oficial de
-- Postgres desde /docker-entrypoint-initdb.d/ y lee las contraseñas de variables de entorno
-- (ver spike/.env.example); nunca van escritas aquí.
-- Estado: sin ejecutar todavía en un Postgres real (se prueba en T029).

CREATE TABLE producto (
  id        integer PRIMARY KEY,
  sku       text NOT NULL UNIQUE,
  nombre    text NOT NULL,
  categoria text NOT NULL,
  precio    numeric(10,2) NOT NULL CHECK (precio >= 0),
  activo    boolean NOT NULL DEFAULT true
);

CREATE TABLE inventario (
  producto_id integer PRIMARY KEY REFERENCES producto(id),
  cantidad    integer NOT NULL CHECK (cantidad >= 0)
);

INSERT INTO producto (id, sku, nombre, categoria, precio, activo) VALUES
  (1, 'POL-NEG-M',  'Polera negra talla M',        'poleras',    8990, true),
  (2, 'POL-BLA-L',  'Polera blanca talla L',       'poleras',    8990, true),
  (3, 'ZAP-BLA-42', 'Zapatillas blancas número 42', 'calzado',   39990, true),
  (4, 'ZAP-NEG-40', 'Zapatillas negras número 40',  'calzado',   39990, true),
  (5, 'MOC-AZU-01', 'Mochila azul',                'accesorios', 24990, true),
  (6, 'GOR-ROJ-01', 'Gorra roja',                  'accesorios',  6990, true),
  (7, 'JEA-AZU-32', 'Jeans azul talla 32',         'pantalones', 29990, true),
  (8, 'CHA-DIS-01', 'Chaqueta discontinuada',      'chaquetas',  49990, false);

INSERT INTO inventario (producto_id, cantidad) VALUES
  (1, 5), (2, 0), (3, 3), (4, 12), (5, 7), (6, 20), (7, 4), (8, 2);

-- Roles. `lector` solo puede leer. `escritor` existe únicamente para demostrar que el esquema
-- permite escribir y que, aun así, `lector` no puede (T031).
\getenv clave_lector POSTGRES_PASSWORD_LECTOR
\getenv clave_escritor POSTGRES_PASSWORD_ESCRITOR

CREATE ROLE lector LOGIN PASSWORD :'clave_lector';
CREATE ROLE escritor LOGIN PASSWORD :'clave_escritor';

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
GRANT SELECT ON producto, inventario TO lector;
GRANT SELECT, INSERT, UPDATE, DELETE ON producto, inventario TO escritor;
