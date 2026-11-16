-- =====================================================================
-- TurnipMarket - Script para SQLite (sin instalar nada)
-- Parte 1: tablas actuales (usuarios, productos) con FK y CHECK
-- Parte 2: tablas propuestas
-- Parte 3: datos de ejemplo
-- Parte 4: consultas CRUD de ejemplo
-- =====================================================================

PRAGMA foreign_keys = ON;   -- sin esto SQLite NO hace cumplir las claves foraneas

DROP TABLE IF EXISTS compras;
DROP TABLE IF EXISTS movimientos;
DROP TABLE IF EXISTS billeteras;
DROP TABLE IF EXISTS denuncias;
DROP TABLE IF EXISTS verificaciones;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS usuarios;

-- ---------------------------------------------------------------------
-- PARTE 1: TABLAS ACTUALES
-- ---------------------------------------------------------------------

CREATE TABLE usuarios (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre               VARCHAR(100) NOT NULL,
    username             VARCHAR(50)  UNIQUE,
    phone                VARCHAR(30),
    email                VARCHAR(255) UNIQUE,
    password             VARCHAR(255) NOT NULL,   -- hash Argon2id
    fecha_creacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verificado           BOOLEAN  NOT NULL DEFAULT 0,
    codigo_verificacion  VARCHAR(6),
    codigo_expiracion    DATETIME,
    alias                VARCHAR(50)  UNIQUE,
    rol                  VARCHAR(20)  NOT NULL DEFAULT 'usuario'
                         CHECK (rol IN ('usuario','moderador','admin')),
    activo               BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id     INTEGER NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     VARCHAR(2000),
    precio          NUMERIC(12,2) NOT NULL CHECK (precio > 0),
    moneda          VARCHAR(3)  NOT NULL DEFAULT 'ARS'       CHECK (moneda IN ('ARS','USD','UYU')),
    categoria       VARCHAR(30) NOT NULL DEFAULT 'other'     CHECK (categoria IN
                    ('electronics','clothing','home','sports','books','vehicles','services','other')),
    condicion       VARCHAR(20) NOT NULL DEFAULT 'new'       CHECK (condicion IN ('new','like_new','good','fair')),
    estado          VARCHAR(20) NOT NULL DEFAULT 'published' CHECK (estado IN ('published','paused','deleted')),
    imagen_url      VARCHAR(500),
    fecha_creacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendedor_id) REFERENCES usuarios (id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX ix_productos_vendedor ON productos (vendedor_id);
CREATE INDEX ix_productos_catalogo ON productos (estado, fecha_creacion);

-- ---------------------------------------------------------------------
-- PARTE 2: TABLAS PROPUESTAS (todavia no existen en el codigo)
-- ---------------------------------------------------------------------

CREATE TABLE verificaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    canal       VARCHAR(10) NOT NULL CHECK (canal IN ('email','sms','discord')),
    fecha       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_id, canal),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE denuncias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    denunciante_id  INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    motivo          VARCHAR(500) NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente','revisada','descartada')),
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (denunciante_id, producto_id),
    FOREIGN KEY (denunciante_id) REFERENCES usuarios  (id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id)    REFERENCES productos (id) ON DELETE CASCADE
);

CREATE TABLE billeteras (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL UNIQUE,                    -- relacion 1:1
    saldo       NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (saldo >= 0),   -- DINERO DE PRUEBA
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT
);

CREATE TABLE movimientos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    billetera_id  INTEGER NOT NULL,
    tipo          VARCHAR(10) NOT NULL CHECK (tipo IN ('recarga','pago','cobro')),
    monto         NUMERIC(12,2) NOT NULL CHECK (monto > 0),
    fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (billetera_id) REFERENCES billeteras (id) ON DELETE RESTRICT
);

CREATE TABLE compras (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    comprador_id  INTEGER NOT NULL,
    producto_id   INTEGER NOT NULL,
    monto         NUMERIC(12,2) NOT NULL CHECK (monto > 0),
    estado        VARCHAR(20) NOT NULL DEFAULT 'pagada' CHECK (estado IN ('pagada','cancelada')),
    fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comprador_id) REFERENCES usuarios  (id) ON DELETE RESTRICT,
    FOREIGN KEY (producto_id)  REFERENCES productos (id) ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- PARTE 3: DATOS DE EJEMPLO (hash de relleno, NO son Argon2id reales)
-- ---------------------------------------------------------------------

INSERT INTO usuarios (nombre, username, email, password, verificado, alias) VALUES
('ana',   'ana',   'ana@ejemplo.com',   '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_ANA',   1, 'ana'),
('bob',   'bob',   'bob@ejemplo.com',   '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_BOB',   1, 'bob'),
('carla', 'carla', 'carla@ejemplo.com', '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_CARLA', 0, 'carla');

INSERT INTO productos (vendedor_id, nombre, descripcion, precio, moneda, categoria, condicion) VALUES
(1, 'Bicicleta rodado 26', 'Bicicleta en buen estado, poco uso',   150000.50, 'ARS', 'sports',      'good'),
(1, 'Notebook usada',      'Notebook 8GB RAM, 256GB SSD',          450000.00, 'ARS', 'electronics', 'like_new'),
(2, 'Libro de calculo',    'Calculo de una variable, 7ma edicion',  25000.00, 'ARS', 'books',       'fair');

INSERT INTO verificaciones (usuario_id, canal) VALUES (1,'email'), (1,'sms'), (2,'email');
INSERT INTO billeteras (usuario_id, saldo) VALUES (1, 0), (2, 0);
INSERT INTO denuncias (denunciante_id, producto_id, motivo) VALUES (2, 1, 'Precio sospechoso');

-- ---------------------------------------------------------------------
-- PARTE 4: CRUD DE EJEMPLO
-- ---------------------------------------------------------------------

-- CREATE
INSERT INTO productos (vendedor_id, nombre, descripcion, precio, categoria)
VALUES (2, 'Mochila escolar', 'Mochila casi nueva', 18000.00, 'other');

-- UPDATE: editar precio solo si el producto es del usuario
UPDATE productos SET precio = 140000.00 WHERE id = 1 AND vendedor_id = 1;

-- UPDATE: pausar publicacion
UPDATE productos SET estado = 'paused' WHERE id = 2 AND vendedor_id = 1;

-- DELETE logico (recomendado)
UPDATE productos SET estado = 'deleted' WHERE id = 3 AND vendedor_id = 2;

-- DELETE fisico de una fila sin relaciones
DELETE FROM productos WHERE nombre = 'Mochila escolar';

-- READ: catalogo publico (solo alias del vendedor, nunca email ni telefono)
SELECT p.id, p.nombre, p.precio, p.moneda, u.alias AS vendedor
FROM productos p
JOIN usuarios u ON u.id = p.vendedor_id
WHERE p.estado = 'published'
ORDER BY p.fecha_creacion DESC;

-- READ: insignia de confianza = cantidad de canales verificados
SELECT u.alias, COUNT(v.id) AS canales_verificados
FROM usuarios u LEFT JOIN verificaciones v ON v.usuario_id = u.id
GROUP BY u.id, u.alias;
