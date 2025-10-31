-- =============================================
-- Script para agregar eliminación lógica (soft delete)
-- a las tablas PREGUNTAS y OPCIONES
-- =============================================

-- Paso 1: Agregar columna vigente a PREGUNTAS
ALTER TABLE PREGUNTAS 
ADD COLUMN vigente TINYINT(1) NOT NULL DEFAULT 1 
COMMENT 'Indica si la pregunta está vigente (1) o fue eliminada lógicamente (0)';

-- Paso 2: Agregar columna vigente a OPCIONES
ALTER TABLE OPCIONES 
ADD COLUMN vigente TINYINT(1) NOT NULL DEFAULT 1
COMMENT 'Indica si la opción está vigente (1) o fue eliminada lógicamente (0)';

-- Paso 3: Marcar todas las preguntas existentes como vigentes
UPDATE PREGUNTAS SET vigente = 1 WHERE vigente IS NULL;

-- Paso 4: Marcar todas las opciones existentes como vigentes
UPDATE OPCIONES SET vigente = 1 WHERE vigente IS NULL;

-- =============================================
-- Verificación
-- =============================================

-- Ver estructura actualizada de PREGUNTAS
DESC PREGUNTAS;

-- Ver estructura actualizada de OPCIONES
DESC OPCIONES;

-- Contar preguntas vigentes vs no vigentes
SELECT 
    vigente,
    COUNT(*) as total,
    CASE 
        WHEN vigente = 1 THEN 'Vigentes'
        WHEN vigente = 0 THEN 'Eliminadas'
        ELSE 'Sin definir'
    END as estado
FROM PREGUNTAS
GROUP BY vigente;

-- Contar opciones vigentes vs no vigentes
SELECT 
    vigente,
    COUNT(*) as total,
    CASE 
        WHEN vigente = 1 THEN 'Vigentes'
        WHEN vigente = 0 THEN 'Eliminadas'
        ELSE 'Sin definir'
    END as estado
FROM OPCIONES
GROUP BY vigente;
