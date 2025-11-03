-- Agregar campo id_usuario_anfitrion a la tabla PARTIDA
-- Este campo guarda quién lanzó/inició la partida (puede ser diferente del creador del cuestionario)

ALTER TABLE PARTIDA 
ADD COLUMN id_usuario_anfitrion INT NULL AFTER id_cuestionario,
ADD CONSTRAINT fk_partida_usuario_anfitrion 
    FOREIGN KEY (id_usuario_anfitrion) 
    REFERENCES USUARIO(id_usuario) 
    ON DELETE SET NULL;

-- Opcional: Actualizar partidas existentes para que el anfitrión sea el creador del cuestionario
UPDATE PARTIDA P
JOIN CUESTIONARIO C ON P.id_cuestionario = C.id_cuestionario
SET P.id_usuario_anfitrion = C.id_usuario
WHERE P.id_usuario_anfitrion IS NULL;
