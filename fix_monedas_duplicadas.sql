-- ========================================
-- FIX: Prevenir duplicación de monedas
-- ========================================
-- Este script agrega protección contra otorgar recompensas múltiples veces
-- Fecha: 28 de octubre de 2025
-- ========================================

-- 1. Agregar columna para controlar si ya se otorgaron recompensas
-- Nota: Si la columna ya existe, este comando dará error (es normal, puedes ignorarlo)
ALTER TABLE PARTIDA 
ADD COLUMN recompensas_otorgadas TINYINT(1) DEFAULT 0 
COMMENT 'Indica si ya se otorgaron recompensas (0=No, 1=Sí)';

-- 2. Marcar partidas finalizadas existentes como "recompensas ya otorgadas"
--    (para evitar problemas con partidas anteriores)
UPDATE PARTIDA 
SET recompensas_otorgadas = 1 
WHERE estado = 'F';

-- 3. OPCIONAL: Verificar el estado de las partidas
SELECT 
    id_partida,
    pin,
    estado,
    recompensas_otorgadas,
    fecha_hora_inicio,
    fecha_hora_fin
FROM PARTIDA
ORDER BY id_partida DESC
LIMIT 20;

-- ========================================
-- CORRECCIÓN DE MONEDAS DUPLICADAS
-- ========================================
-- Si necesitas corregir monedas que se duplicaron, 
-- deberás ejecutar esto MANUALMENTE después de calcular:
--
-- 1. Identificar usuarios afectados
-- 2. Calcular cuántas monedas deberían tener
-- 3. Actualizar manualmente:
--
-- UPDATE USUARIO
-- SET monedas = [cantidad_correcta]
-- WHERE id_usuario = [id];
-- ========================================

-- NOTAS:
-- - La protección ahora evita que se otorguen recompensas 2 veces
-- - Las partidas anteriores (ya finalizadas) están marcadas como "recompensas otorgadas"
-- - Nuevas partidas funcionarán correctamente con esta protección
