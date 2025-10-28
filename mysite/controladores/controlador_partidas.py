from bd import obtener_conexion
from controladores import controlador_recompensas as c_rec
from datetime import datetime
import random
import string
import pymysql
import re
from datetime import datetime

def _generar_pin():
    """Genera un código aleatorio de 6 caracteres (mayúsculas y números)."""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choices(caracteres, k=6))

def verificar_partida_activa(id_cuestionario):
    """
    Verifica si ya existe una partida activa (en Espera 'E' o Proceso 'P')
    para un cuestionario específico. Devuelve True si existe, False si no.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Buscamos partidas que NO estén finalizadas ('F')
            sql = "SELECT id_partida FROM PARTIDA WHERE id_cuestionario = %s AND estado != 'F'"
            cursor.execute(sql, (id_cuestionario,))
            partida_activa = cursor.fetchone()

            # Si fetchone() encuentra algo, significa que ya hay una partida activa
            return partida_activa is not None
    finally:
        if conexion:
            conexion.close()


def crear_partida(id_cuestionario, modalidad_grupal=False, cant_grupos=None):
    """
    Crea una nueva partida, guardando la cantidad de grupos si es necesario.
    Devuelve (True, pin) en caso de éxito, o (False, "mensaje de error").
    """
    # 1. Verificamos que no haya otra partida en curso
    if verificar_partida_activa(id_cuestionario):
        return False, "Ya existe una partida activa para este cuestionario. Finalízala antes de crear una nueva."

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 2. Generamos un PIN único
            pin = _generar_pin()
            while True:
                cursor.execute("SELECT id_partida FROM PARTIDA WHERE pin = %s", (pin,))
                if not cursor.fetchone():
                    break
                pin = _generar_pin()

            # --- ¡CAMBIOS AQUÍ! ---
            # 3. Insertamos la nueva partida, incluyendo cant_grupos
            sql = """
                INSERT INTO PARTIDA (pin, id_cuestionario, modalidad, estado, fecha_hora_inicio, fecha_hora_fin, cant_grupos)
                VALUES (%s, %s, %s, 'E', %s, NULL, %s)
            """

            # Si la modalidad no es grupal, nos aseguramos de que cant_grupos sea NULL
            grupos_para_db = cant_grupos if modalidad_grupal else None

            cursor.execute(sql, (pin, id_cuestionario, modalidad_grupal, datetime.now(), grupos_para_db))

        conexion.commit()
        return True, pin
    except Exception as e:
        conexion.rollback()
        print(f"Error al crear partida: {e}")
        return False, "Ocurrió un error al crear la partida."
    finally:
        if conexion:
            conexion.close()


def obtener_partidas_por_usuario(id_usuario):
    """
    Obtiene una lista de todas las partidas (activas y finalizadas)
    de los cuestionarios que pertenecen a un usuario.
    """
    conexion = obtener_conexion()
    partidas = []
    try:
        with conexion.cursor() as cursor:
            # Hacemos un JOIN para vincular Partida -> Cuestionario -> Usuario
            sql = """
                SELECT
                    P.id_partida, P.pin, P.estado, P.fecha_hora_inicio, P.modalidad,
                    C.titulo AS cuestionario_titulo
                FROM PARTIDA AS P
                JOIN CUESTIONARIO AS C ON P.id_cuestionario = C.id_cuestionario
                WHERE C.id_usuario = %s
                ORDER BY P.fecha_hora_inicio DESC
            """
            cursor.execute(sql, (id_usuario,))
            partidas = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return partidas




def finalizar_partida(id_partida, ranking_data=None):
    """
    Finaliza una partida y otorga recompensas.
    
    Args:
        id_partida: ID de la partida
        ranking_data: Lista opcional con {'id_usuario', 'puntaje', 'posicion'}
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Actualizamos estado y fecha de fin
        cursor.execute("""
            UPDATE PARTIDA
            SET estado = 'F', fecha_hora_fin = NOW()
            WHERE id_partida = %s
        """, (id_partida,))
        conexion.commit()

        # Otorgar recompensas después de finalizar (con ranking si se proporciona)
        exito = c_rec.otorgar_recompensas(id_partida, ranking_data)

        if exito:
            print(f"Partida {id_partida} finalizada y recompensas otorgadas correctamente")
        else:
            print(f"Partida {id_partida} finalizada, pero hubo un problema al otorgar recompensas")

        return True

    except Exception as e:
        conexion.rollback()
        print(f"Error al finalizar partida: {e}")
        return False

    finally:
        cursor.close()
        conexion.close()


# ----------------------------------
def obtener_partida_por_pin(pin: str):
    cn = obtener_conexion()
    try:
        with cn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT
                    id_partida,
                    pin,
                    CASE estado
                        WHEN 'F' THEN 'FINALIZADA'
                        WHEN 'E' THEN 'EN_CURSO'
                        WHEN 'P' THEN 'CREADA'
                        ELSE estado
                    END AS estado,
                    fecha_hora_inicio AS fecha_inicio,
                    fecha_hora_fin    AS fecha_fin,
                    id_cuestionario
                FROM PARTIDA
                WHERE pin = %s
                LIMIT 1
            """, (pin.upper(),))
            row = cur.fetchone()
            return row
    finally:
        cn.close()

# def obtener_partida_por_pin(pin):
#     """
#     Obtiene los datos de una partida usando su PIN.
#     Esencial para inicializar el estado del juego en memoria.
#     """
#     conexion = obtener_conexion()
#     partida = None
#     try:
#         with conexion.cursor() as cursor:
#             # Seleccionamos los datos clave de la partida
#             sql = "SELECT id_partida, id_cuestionario, modalidad, cant_grupos FROM PARTIDA WHERE pin = %s AND estado = 'E'"
#             cursor.execute(sql, (pin,))
#             partida = cursor.fetchone()
#     finally:
#         if conexion:
#             conexion.close()
#     return partida

import pymysql
# ...

def obtener_partida_por_pin(pin: str):
    cn = obtener_conexion()
    try:
        with cn.cursor(pymysql.cursors.DictCursor) as cur:  # <-- cambio aquí
            cur.execute("""
                SELECT
                    id_partida,
                    pin,
                    CASE estado
                        WHEN 'F' THEN 'FINALIZADA'
                        WHEN 'E' THEN 'EN_CURSO'
                        WHEN 'P' THEN 'CREADA'
                        ELSE estado
                    END AS estado,
                    fecha_hora_inicio AS fecha_inicio,
                    fecha_hora_fin    AS fecha_fin,
                    id_cuestionario,
                    modalidad,          -- ★ necesario para _ensure_loaded
                    cant_grupos         -- ★ necesario para _ensure_loaded
                FROM PARTIDA
                WHERE pin = %s
                LIMIT 1
            """, (pin.upper(),))
            row = cur.fetchone()
            if not row:
                return None
            row["modalidad"]   = bool(row.get("modalidad"))
            row["cant_grupos"] = int(row["cant_grupos"]) if row.get("cant_grupos") is not None else None
            return row
    finally:
        cn.close()


def obtener_opcion_por_id(id_opcion):
    conexion = obtener_conexion()
    opcion = None
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM OPCIONES WHERE id_opcion = %s", (id_opcion,))
            opcion = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return opcion

# ---------------------------------- Helpers
def _extraer_numero_grupo(nombre_grupo):
    """
    Devuelve el número de grupo detectado en el nombre del grupo (ej: 'Grupo 2' -> 2).
    Si no hay número, retorna 0.
    """
    if not nombre_grupo:
        return 0
    match = re.search(r"\d+", str(nombre_grupo))
    if match:
        try:
            return int(match.group())
        except ValueError:
            return 0
    return 0

# ---------------------------------- AGREGADO POR PAME - Reportes
def log_respuesta_en_bd(partida, participante, pregunta, opcion_db, puntos, tiempo_restante, nombre_usuario):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(pymysql.cursors.DictCursor) as c:
            modalidad_grupal = bool(partida.get('modalidad_grupal'))
            numero_grupo = 0
            if modalidad_grupal:
                numero_grupo = int(participante.get('grupo_numero') or 0)
                if not numero_grupo:
                    numero_grupo = _extraer_numero_grupo(participante.get('grupo'))
                    if not numero_grupo:
                        grupos = partida.get('grupos') or []
                        for grupo in grupos:
                            if grupo.get('nombre') == participante.get('grupo'):
                                numero_grupo = int(grupo.get('numero') or 0)
                                break
            numero_grupo = numero_grupo or 0

            # UPSERT (dispara por uniq_partida_usuario o uniq_partida_nombre)
            c.execute("""
                INSERT INTO PARTICIPANTE (id_partida, id_usuario, nombre, id_grupo, grupo, puntaje, registrado)
                VALUES (%s, %s, %s, %s, %s, 0, %s)
                ON DUPLICATE KEY UPDATE id_grupo = VALUES(id_grupo),
                                        grupo = VALUES(grupo)
            """, (
                partida['id_partida'],
                participante.get('id_usuario'),
                nombre_usuario,
                None,
                numero_grupo,
                1 if participante.get('id_usuario') else 0
            ))

            c.execute("""
                SELECT id_participante
                FROM PARTICIPANTE
                WHERE id_partida=%s AND nombre=%s
                LIMIT 1
            """, (partida['id_partida'], nombre_usuario))
            row = c.fetchone()
            if not row:
                conexion.rollback()
                return False
            id_participante = row['id_participante']

            seg_usados = int(max(0, (pregunta.get('tiempo') or 0) - (tiempo_restante or 0)))
            
            c.execute("""
                INSERT INTO RESPUESTA_PARTICIPANTE
                (id_partida, id_participante, id_pregunta, id_opcion,
                pregunta_texto, opcion_texto, es_correcta, puntaje, tiempo_respuesta)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s, SEC_TO_TIME(%s))
            """, (
                partida['id_partida'],
                id_participante,
                pregunta['id_pregunta'],
                opcion_db['id_opcion'],
                pregunta['pregunta'],
                opcion_db['opcion'],
                1 if opcion_db.get('es_correcta_bool') else 0,
                int(puntos),
                seg_usados
            ))

        conexion.commit()
        return True
    
    except Exception as e:  # <-- CORREGIDO: agregada variable 'e'
        try:
            if conexion:
                conexion.rollback()
        except Exception:
            pass
        print(f"[log_respuesta_en_bd] Error: {e}")
        return False
    finally:
        try:
            if conexion:
                conexion.close()
        except Exception:
            pass


def _get_partida_by_pin(pin):
    """Devuelve info básica de la partida por PIN (id_partida, cuestionario, fechas, estado)."""
    cx = obtener_conexion()
    try:
        with cx.cursor(pymysql.cursors.DictCursor) as c:
            c.execute("""
                SELECT  p.id_partida, p.pin, p.estado, p.fecha_hora_inicio, p.fecha_hora_fin,
                        p.id_cuestionario, c.titulo AS cuestionario_titulo
                        FROM PARTIDA p
                        JOIN CUESTIONARIO c ON c.id_cuestionario = p.id_cuestionario
                        WHERE p.pin = %s
                        LIMIT 1
            """, (pin.upper(),)) 
            return c.fetchone()
    finally:
        cx.close()

def _get_partida_header(id_partida):
    """Encabezado del reporte: datos de la partida y cuestionario."""
    cx = obtener_conexion()
    try:
        with cx.cursor(pymysql.cursors.DictCursor) as c:
            c.execute("""
                SELECT  p.id_partida, p.pin, p.estado, p.fecha_hora_inicio, p.fecha_hora_fin,
                        p.id_cuestionario, c.titulo AS cuestionario_titulo
                        FROM PARTIDA p
                        JOIN CUESTIONARIO c ON c.id_cuestionario = p.id_cuestionario
                        WHERE p.id_partida = %s
                        LIMIT 1
            """, (id_partida,))
            return c.fetchone()
    finally:
        cx.close()

def _get_resumen_global(id_partida):
    """
    Resumen numérico: participantes, preguntas, respuestas totales,
    % acierto global y tiempo promedio de respuesta (en segundos).
    """
    cx = obtener_conexion()
    try:
        with cx.cursor(pymysql.cursors.DictCursor) as c:
            # participantes que respondieron al menos una pregunta
            c.execute(
                """
                SELECT COUNT(DISTINCT id_participante) AS total
                    FROM RESPUESTA_PARTICIPANTE
                    WHERE id_partida=%s
            """,
                (id_partida,),
            )
            total_participantes = c.fetchone()["total"]

            # preguntas distintas que recibieron respuesta
            c.execute(
                """
                SELECT COUNT(DISTINCT id_pregunta) AS total
                    FROM RESPUESTA_PARTICIPANTE
                    WHERE id_partida=%s
            """,
                (id_partida,),
            )
            preguntas_distintas = c.fetchone()["total"]

            # respuestas totales
            c.execute(
                """
                SELECT COUNT(*) AS total
                    FROM RESPUESTA_PARTICIPANTE
                    WHERE id_partida=%s
            """,
                (id_partida,),
            )
            respuestas_totales = c.fetchone()["total"]

            # acierto global y tiempo promedio
            c.execute(
                """
                SELECT AVG(es_correcta+0) AS acierto_prom,
                       AVG(TIME_TO_SEC(tiempo_respuesta)) AS tiempo_prom
                    FROM RESPUESTA_PARTICIPANTE
                    WHERE id_partida=%s
            """,
                (id_partida,),
            )
            row = c.fetchone()
            acierto_global = float(row["acierto_prom"] or 0.0)  # 0..1
            tiempo_prom_seg = float(row["tiempo_prom"] or 0.0)

        return {
            "total_participantes": total_participantes,
            "preguntas_distintas": preguntas_distintas,
            "respuestas_totales": respuestas_totales,
            "acierto_global": round(acierto_global * 100, 2),
            "tiempo_promedio_seg": round(tiempo_prom_seg, 2),
        }
    finally:
        cx.close()

def _get_ranking_final(id_partida):
    """
    Ranking final por participante (modo individual) calculado desde RESPUESTA_PARTICIPANTE
    sumando puntajes. Si usas modalidad grupal y guardas a detalle, igual sirve para ver top.
    """
    cx = obtener_conexion()
    try:
        with cx.cursor(pymysql.cursors.DictCursor) as c:
            c.execute("""
                SELECT pa.nombre,
                        COALESCE(pa.grupo, 0) AS grupo,
                        SUM(rp.puntaje) AS puntaje_total,
                        SUM(rp.es_correcta+0) AS correctas,
                        COUNT(*) - SUM(rp.es_correcta+0) AS incorrectas,
                        AVG(TIME_TO_SEC(rp.tiempo_respuesta)) AS tiempo_prom_seg
                    FROM RESPUESTA_PARTICIPANTE rp
                    JOIN PARTICIPANTE pa ON pa.id_participante = rp.id_participante
                    WHERE rp.id_partida=%s
                    GROUP BY pa.id_participante, pa.nombre, pa.grupo
                    ORDER BY puntaje_total DESC, correctas DESC
            """, (id_partida,))
            return c.fetchall()
    finally:
        cx.close()

def _get_detalle_preguntas(id_partida):
    cx = obtener_conexion()
    try:
        with cx.cursor(pymysql.cursors.DictCursor) as c:
            # Sin ANY_VALUE: usa MIN que es determinístico para un mismo texto
            c.execute("""
                SELECT  rp.id_pregunta,
                        MIN(rp.pregunta_texto) AS pregunta_texto,
                        ROUND(AVG(rp.es_correcta+0)*100,2) AS porcentaje_acierto,
                        ROUND(AVG(TIME_TO_SEC(rp.tiempo_respuesta)),2) AS tiempo_promedio_seg,
                        COUNT(*) AS respuestas
                    FROM RESPUESTA_PARTICIPANTE rp
                    WHERE rp.id_partida=%s
                    GROUP BY rp.id_pregunta
                    ORDER BY rp.id_pregunta
            """, (id_partida,))
            base = c.fetchall()

            # Texto de opción correcta
            for item in base:
                c.execute("""
                    SELECT opcion_texto
                        FROM RESPUESTA_PARTICIPANTE
                        WHERE id_partida=%s AND id_pregunta=%s AND es_correcta=1
                        LIMIT 1
                """, (id_partida, item["id_pregunta"]))
                row = c.fetchone()
                item["opcion_correcta"] = row["opcion_texto"] if row else None

            return base
    finally:
        cx.close()


def _get_detalle_participantes(id_partida):
    """
    Métricas por participante: puntaje total, correctas, incorrectas, tiempo promedio.
    (Similar al ranking pero sin ordenar, o puedes mantener el orden por puntaje).
    """
    return _get_ranking_final(id_partida)

def reporte_por_partida_id(id_partida):
    """
    Construye un dict con todo el reporte:
    - header: datos generales
    - resumen: KPIs globales
    - preguntas: métricas por pregunta
    - participantes: métricas por participante (ranking)
    """
    header = _get_partida_header(id_partida)
    if not header:
        return None

    resumen = _get_resumen_global(id_partida)
    preguntas = _get_detalle_preguntas(id_partida)
    participantes = _get_detalle_participantes(id_partida)

    return {
        "header": header,
        "resumen": resumen,
        "preguntas": preguntas,
        "participantes": participantes
    }


def reporte_por_pin(pin):
    """Conveniencia: obtiene id_partida por PIN y arma el reporte completo."""
    p = _get_partida_by_pin(pin)
    if not p:
        return None
    return reporte_por_partida_id(p["id_partida"])

# ---------------------------------- AGREGADO POR PAME - Reportes
