from bd import obtener_conexion
from controladores import controlador_recompensas as c_rec
from datetime import datetime
import random
import string

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
                    P.id_partida, P.pin, P.estado, P.fecha_hora_inicio,
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




def finalizar_partida(id_partida):
    """Finaliza una partida y otorga recompensas."""
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

        # Otorgar recompensas después de finalizar
        exito = c_rec.otorgar_recompensas(id_partida)

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
def obtener_partida_por_pin(pin):
    """
    Obtiene los datos de una partida usando su PIN.
    Esencial para inicializar el estado del juego en memoria.
    """
    conexion = obtener_conexion()
    partida = None
    try:
        with conexion.cursor() as cursor:
            # Seleccionamos los datos clave de la partida
            sql = "SELECT id_partida, id_cuestionario, modalidad, cant_grupos FROM PARTIDA WHERE pin = %s AND estado = 'E'"
            cursor.execute(sql, (pin,))
            partida = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return partida


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

