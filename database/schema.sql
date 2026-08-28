CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    username TEXT UNIQUE,
    phone TEXT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verificado INTEGER DEFAULT 0,
    codigo_verificacion TEXT,
    codigo_expiracion TIMESTAMP,
    alias TEXT UNIQUE
);
