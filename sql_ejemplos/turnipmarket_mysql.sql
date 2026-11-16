-- =====================================================================
-- TurnipMarket - Script para MySQL Workbench (MySQL 8.0.16 o superior)
-- Parte 1: tablas actuales (usuarios, productos) con FK y CHECK
-- Parte 2: tablas propuestas (verificaciones, denuncias, billeteras,
--          movimientos, compras)
-- Parte 3: datos de ejemplo
-- Parte 4: CRUD de ejemplo
-- =====================================================================

-- Crea una base nueva (requiere un usuario con permisos, por ejemplo root).
CREATE DATABASE IF NOT EXISTS turnipmarket CHARACTER SET utf8mb4;
USE turnipmarket;

-- Limpia SOLO las tablas de este script (orden inverso por las FK)
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
    id                   INT          NOT NULL AUTO_INCREMENT,
    nombre               VARCHAR(100) NOT NULL,
    username             VARCHAR(50)  NULL,
    phone                VARCHAR(30)  NULL,
    email                VARCHAR(255) NULL,
    password             VARCHAR(255) NOT NULL COMMENT 'Hash Argon2id, nunca la clave en claro',
    fecha_creacion       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verificado           TINYINT(1)   NOT NULL DEFAULT 0,
    codigo_verificacion  VARCHAR(6)   NULL,
    codigo_expiracion    DATETIME     NULL,
    alias                VARCHAR(50)  NULL,
    -- campos propuestos para el panel de moderadores (RF09)
    rol                  VARCHAR(20)  NOT NULL DEFAULT 'usuario',
    activo               TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_username (username),
    UNIQUE KEY uq_usuarios_email    (email),
    UNIQUE KEY uq_usuarios_alias    (alias),
    CONSTRAINT ck_usuarios_rol CHECK (rol IN ('usuario', 'moderador', 'admin'))
) ENGINE=InnoDB;

CREATE TABLE productos (
    id              INT           NOT NULL AUTO_INCREMENT,
    vendedor_id     INT           NOT NULL,
    nombre          VARCHAR(150)  NOT NULL,
    descripcion     VARCHAR(2000) NULL,
    precio          DECIMAL(12,2) NOT NULL,
    moneda          VARCHAR(3)    NOT NULL DEFAULT 'ARS',
    categoria       VARCHAR(30)   NOT NULL DEFAULT 'other',
    condicion       VARCHAR(20)   NOT NULL DEFAULT 'new',
    estado          VARCHAR(20)   NOT NULL DEFAULT 'published',
    imagen_url      VARCHAR(500)  NULL,
    fecha_creacion  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_productos_vendedor (vendedor_id),
    KEY ix_productos_catalogo (estado, fecha_creacion),
    -- Relacion 1:N. RESTRICT: no se puede borrar un usuario que tiene productos.
    CONSTRAINT fk_productos_vendedor
        FOREIGN KEY (vendedor_id) REFERENCES usuarios (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_productos_precio    CHECK (precio > 0),
    CONSTRAINT ck_productos_moneda    CHECK (moneda IN ('ARS','USD','UYU')),
    CONSTRAINT ck_productos_categoria CHECK (categoria IN
        ('electronics','clothing','home','sports','books','vehicles','services','other')),
    CONSTRAINT ck_productos_condicion CHECK (condicion IN ('new','like_new','good','fair')),
    CONSTRAINT ck_productos_estado    CHECK (estado IN ('published','paused','deleted'))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- PARTE 2: TABLAS PROPUESTAS (todavia no existen en el codigo)
-- ---------------------------------------------------------------------

-- RF02 y RF04: una fila por canal verificado; la insignia se calcula contando filas
CREATE TABLE verificaciones (
    id          INT         NOT NULL AUTO_INCREMENT,
    usuario_id  INT         NOT NULL,
    canal       VARCHAR(10) NOT NULL,
    fecha       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_verificacion_canal (usuario_id, canal),
    CONSTRAINT fk_verif_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT ck_verif_canal CHECK (canal IN ('email','sms','discord'))
) ENGINE=InnoDB;

-- RF08 y RF09: denuncias de publicaciones
CREATE TABLE denuncias (
    id              INT           NOT NULL AUTO_INCREMENT,
    denunciante_id  INT           NOT NULL,
    producto_id     INT           NOT NULL,
    motivo          VARCHAR(500)  NOT NULL,
    estado          VARCHAR(20)   NOT NULL DEFAULT 'pendiente',
    fecha           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_denuncia (denunciante_id, producto_id),
    CONSTRAINT fk_den_usuario  FOREIGN KEY (denunciante_id) REFERENCES usuarios  (id) ON DELETE CASCADE,
    CONSTRAINT fk_den_producto FOREIGN KEY (producto_id)    REFERENCES productos (id) ON DELETE CASCADE,
    CONSTRAINT ck_den_estado CHECK (estado IN ('pendiente','revisada','descartada'))
) ENGINE=InnoDB;

-- RF10: billetera con dinero ficticio (relacion 1:1 con usuarios)
CREATE TABLE billeteras (
    id          INT           NOT NULL AUTO_INCREMENT,
    usuario_id  INT           NOT NULL,
    saldo       DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT 'DINERO DE PRUEBA, NO ES REAL',
    PRIMARY KEY (id),
    UNIQUE KEY uq_billetera_usuario (usuario_id),
    CONSTRAINT fk_bill_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT,
    CONSTRAINT ck_saldo_no_negativo CHECK (saldo >= 0)
) ENGINE=InnoDB;

CREATE TABLE movimientos (
    id           INT           NOT NULL AUTO_INCREMENT,
    billetera_id INT           NOT NULL,
    tipo         VARCHAR(10)   NOT NULL,
    monto        DECIMAL(12,2) NOT NULL,
    fecha        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_mov_billetera (billetera_id),
    CONSTRAINT fk_mov_billetera FOREIGN KEY (billetera_id) REFERENCES billeteras (id) ON DELETE RESTRICT,
    CONSTRAINT ck_mov_tipo  CHECK (tipo IN ('recarga','pago','cobro')),
    CONSTRAINT ck_mov_monto CHECK (monto > 0)
) ENGINE=InnoDB;

-- Pasarela simulada: relacion muchos a muchos entre usuarios y productos
CREATE TABLE compras (
    id            INT           NOT NULL AUTO_INCREMENT,
    comprador_id  INT           NOT NULL,
    producto_id   INT           NOT NULL,
    monto         DECIMAL(12,2) NOT NULL,
    estado        VARCHAR(20)   NOT NULL DEFAULT 'pagada',
    fecha         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_compras_comprador (comprador_id),
    KEY ix_compras_producto  (producto_id),
    CONSTRAINT fk_compra_comprador FOREIGN KEY (comprador_id) REFERENCES usuarios  (id) ON DELETE RESTRICT,
    CONSTRAINT fk_compra_producto  FOREIGN KEY (producto_id)  REFERENCES productos (id) ON DELETE RESTRICT,
    CONSTRAINT ck_compra_monto  CHECK (monto > 0),
    CONSTRAINT ck_compra_estado CHECK (estado IN ('pagada','cancelada'))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- PARTE 3: DATOS DE EJEMPLO
-- (los hash son de relleno, NO son hashes Argon2id reales)
-- ---------------------------------------------------------------------

INSERT INTO usuarios (nombre, username, email, password, verificado, alias) VALUES
('ana',   'ana',   'ana@ejemplo.com',   '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_ANA',   1, 'ana'),
('bob',   'bob',   'bob@ejemplo.com',   '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_BOB',   1, 'bob'),
('carla', 'carla', 'carla@ejemplo.com', '$argon2id$v=19$m=65536,t=3,p=4$RELLENO_CARLA', 0, 'carla');

INSERT INTO productos (vendedor_id, nombre, descripcion, precio, moneda, categoria, condicion) VALUES
(1, 'Bicicleta rodado 26', 'Bicicleta en buen estado, poco uso', 150000.50, 'ARS', 'sports',      'good'),
(1, 'Notebook usada',      'Notebook 8GB RAM, 256GB SSD',        450000.00, 'ARS', 'electronics', 'like_new'),
(2, 'Libro de calculo',    'Calculo de una variable, 7ma edicion', 25000.00, 'ARS', 'books',      'fair');

INSERT INTO verificaciones (usuario_id, canal) VALUES (1,'email'), (1,'sms'), (2,'email');
INSERT INTO billeteras (usuario_id, saldo) VALUES (1, 0), (2, 0);
INSERT INTO denuncias (denunciante_id, producto_id, motivo) VALUES (2, 1, 'Precio sospechoso');

-- ---------------------------------------------------------------------
-- PARTE 4: CRUD DE EJEMPLO
-- ---------------------------------------------------------------------

-- CREATE
INSERT INTO productos (vendedor_id, nombre, descripcion, precio, categoria)
VALUES (2, 'Mochila escolar', 'Mochila casi nueva', 18000.00, 'other');

-- READ: catalogo publico (solo alias del vendedor, nunca email ni telefono)
SELECT p.id, p.nombre, p.precio, p.moneda, u.alias AS vendedor
FROM productos p
JOIN usuarios u ON u.id = p.vendedor_id
WHERE p.estado = 'published'
ORDER BY p.fecha_creacion DESC;

-- READ: mis publicaciones
SELECT id, nombre, precio, estado FROM productos WHERE vendedor_id = 1;

-- READ: insignia de confianza = cantidad de canales verificados
SELECT u.alias, COUNT(v.id) AS canales_verificados
FROM usuarios u LEFT JOIN verificaciones v ON v.usuario_id = u.id
GROUP BY u.id, u.alias;

-- UPDATE: editar precio solo si el producto es del usuario
UPDATE productos SET precio = 140000.00 WHERE id = 1 AND vendedor_id = 1;

-- UPDATE: pausar publicacion
UPDATE productos SET estado = 'paused' WHERE id = 2 AND vendedor_id = 1;

-- DELETE logico (recomendado)
UPDATE productos SET estado = 'deleted' WHERE id = 3 AND vendedor_id = 2;

-- DELETE fisico de una fila sin relaciones
DELETE FROM productos WHERE nombre = 'Mochila escolar';

-- Recarga ficticia con transaccion (RF10)
START TRANSACTION;
UPDATE billeteras SET saldo = saldo + 10000 WHERE usuario_id = 1;
INSERT INTO movimientos (billetera_id, tipo, monto)
SELECT id, 'recarga', 10000 FROM billeteras WHERE usuario_id = 1;
COMMIT;

-- ---------------------------------------------------------------------
-- PRUEBAS DE INTEGRIDAD: cada una debe FALLAR (descomentar de a una)
-- ---------------------------------------------------------------------
-- INSERT INTO productos (vendedor_id, nombre, precio) VALUES (9999, 'Fantasma', 10);   -- FK
-- INSERT INTO productos (vendedor_id, nombre, precio) VALUES (1, 'Negativo', -5);      -- CHECK precio
-- INSERT INTO productos (vendedor_id, nombre, precio, categoria) VALUES (1,'Raro',5,'XYZ'); -- CHECK categoria
-- DELETE FROM usuarios WHERE id = 1;                                                   -- RESTRICT
-- INSERT INTO usuarios (nombre, email, password) VALUES ('x','ana@ejemplo.com','x');   -- UNIQUE email

-- Ver todo
SHOW TABLES;
