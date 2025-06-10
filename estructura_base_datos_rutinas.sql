
-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    nombre_clave TEXT PRIMARY KEY
);

-- Tabla de rutinas (cada usuario puede tener varias rutinas)
CREATE TABLE IF NOT EXISTS rutinas (
    id_rutina SERIAL PRIMARY KEY,
    nombre_clave TEXT REFERENCES usuarios(nombre_clave),
    nombre_rutina TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detalle de ejercicios en cada rutina
CREATE TABLE IF NOT EXISTS detalle_rutina (
    id SERIAL PRIMARY KEY,
    id_rutina INTEGER REFERENCES rutinas(id_rutina),
    id_ejercicio INTEGER,
    repeticiones INTEGER,
    series INTEGER
);
