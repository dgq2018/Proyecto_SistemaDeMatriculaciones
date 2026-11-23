-- ==============================================
-- ESTRUCTURA COMPLETA DEL SISTEMA DE MATRICULAS
-- ==============================================

CREATE DATABASE proyecto_matriculaciones

-- 1. ELIMINACIÓN DE TABLAS 
DROP TABLE IF EXISTS backups_sistema;
DROP TABLE IF EXISTS historial_nominas; 
DROP TABLE IF EXISTS inscripciones;
DROP TABLE IF EXISTS estudiantes;
DROP TABLE IF EXISTS grados;
DROP TABLE IF EXISTS periodos;

-- 2. PERIODOS
CREATE TABLE periodos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    anio INTEGER UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT FALSE,
    estado VARCHAR(20) DEFAULT 'abierto'
);

-- 3. ESTUDIANTES
CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    documento VARCHAR(20) UNIQUE NOT NULL,
    fecha_nacimiento DATE,
    activo BOOLEAN DEFAULT TRUE
);

-- 4. GRADOS (Con relación recursiva incluida)
CREATE TABLE grados (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    orden INT DEFAULT 0,
    siguiente_grado_id INTEGER REFERENCES grados(id) ON DELETE SET NULL
);

-- 5. INSCRIPCIONES
CREATE TABLE inscripciones (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE RESTRICT,
    grado_id INTEGER REFERENCES grados(id) ON DELETE CASCADE,
    periodo_id INTEGER REFERENCES periodos(id) ON DELETE CASCADE,
    fecha_inscripcion DATE DEFAULT CURRENT_DATE,
    UNIQUE (estudiante_id, periodo_id)
);

-- 6. HISTORIAL (Snapshots)
CREATE TABLE historial_nominas (
    id SERIAL PRIMARY KEY,
    periodo_id INTEGER REFERENCES periodos(id) ON DELETE CASCADE,
    grado_id INTEGER REFERENCES grados(id) ON DELETE CASCADE,
    nominas_json JSONB NOT NULL,
    fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. SEGURIDAD (Backups)
CREATE TABLE backups_sistema (
    id SERIAL PRIMARY KEY,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    datos_json JSONB NOT NULL,
    descripcion TEXT
);

-----------------------------SELECT-------------------------------
select * from estudiantes;
select * from historial_nominas;
select * from inscripciones;
select * from periodos;
SELECT * from grados;
select * from backups_sistema;



