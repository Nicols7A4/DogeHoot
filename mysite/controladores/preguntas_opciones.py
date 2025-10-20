# controladores/preguntas_opciones.py
import os
from main import app
from bd import obtener_conexion

# --- Lógica de Preguntas ---
def crear_pregunta(id_cuestionario, pregunta, num_pregunta, puntaje_base, adjunto=None):
    """Crea una nueva pregunta para un cuestionario."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, adjunto) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (id_cuestionario, pregunta, num_pregunta, puntaje_base, adjunto))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()


def obtener_preguntas_por_cuestionario(id_cuestionario):
    """Obtiene todas las preguntas de un cuestionario específico."""
    conexion = obtener_conexion()
    preguntas = []
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s ORDER BY num_pregunta ASC", (id_cuestionario,))
            preguntas = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return preguntas


def obtener_pregunta_por_id(id_pregunta):
    """Obtiene una única pregunta por su ID."""
    conexion = obtener_conexion()
    pregunta = None
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM PREGUNTAS WHERE id_pregunta = %s", (id_pregunta,))
            pregunta = cursor.fetchone()
    finally:
        conexion.close()
    return pregunta


def actualizar_pregunta(id_pregunta, pregunta_texto, puntaje_base):
    """Actualiza el texto y puntaje de una pregunta."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE PREGUNTAS SET pregunta = %s, puntaje_base = %s WHERE id_pregunta = %s"
            cursor.execute(sql, (pregunta_texto, puntaje_base, id_pregunta))
        conexion.commit()
    finally:
        conexion.close()


def eliminar_pregunta(id_pregunta):
    """Elimina una pregunta (y sus opciones gracias a ON DELETE CASCADE)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM PREGUNTAS WHERE id_pregunta = %s", (id_pregunta,))
        conexion.commit()
    finally:
        conexion.close()




def actualizar_ruta_imagen(id_pregunta, ruta_img):
    """Actualiza la ruta de la imagen para una pregunta específica."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s"
            cursor.execute(sql, (ruta_img, id_pregunta))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()


def quitar_imagen_pregunta(id_pregunta):
    """
    Elimina la referencia de la imagen de la base de datos y borra el archivo físico del servidor.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 1. Obtenemos la ruta de la imagen actual para saber qué borrar
            cursor.execute("SELECT adjunto FROM PREGUNTAS WHERE id_pregunta = %s", (id_pregunta,))
            resultado = cursor.fetchone()
            ruta_img_relativa = resultado.get('adjunto') if resultado else None

            # 2. Actualizamos la base de datos para poner la ruta en NULL
            sql = "UPDATE PREGUNTAS SET adjunto = NULL WHERE id_pregunta = %s"
            cursor.execute(sql, (id_pregunta,))
        conexion.commit()

        # 3. Si existía una ruta, borramos el archivo físico del servidor
        if ruta_img_relativa:
            try:
                # Construimos la ruta absoluta al archivo
                ruta_completa = os.path.join(app.root_path, 'static', ruta_img_relativa)
                if os.path.exists(ruta_completa):
                    os.remove(ruta_completa)
                    print(f"Archivo eliminado: {ruta_completa}")
            except Exception as e:
                # Si falla el borrado del archivo, no es crítico, pero lo registramos
                print(f"Error al borrar el archivo físico: {e}")

        return True
    except Exception as e:
        conexion.rollback()
        print(f"Error al quitar la imagen en la BD: {e}")
        return False
    finally:
        if conexion:
            conexion.close()






# --- Lógica de Opciones ---
def crear_opcion(id_pregunta, opcion, es_correcta_bool, descripcion=None, adjunto=None):
    """Crea una nueva opción para una pregunta."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()

def obtener_opciones_por_pregunta(id_pregunta):
    """Obtiene todas las opciones de una pregunta específica."""
    conexion = obtener_conexion()
    opciones = []
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM OPCIONES WHERE id_pregunta = %s", (id_pregunta,))
            opciones = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return opciones


def obtener_opcion_por_id(id_opcion):
    """Obtiene una única opción por su ID."""
    conexion = obtener_conexion()
    opcion = None
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM OPCIONES WHERE id_opcion = %s", (id_opcion,))
            opcion = cursor.fetchone()
    finally:
        conexion.close()
    return opcion

def actualizar_opcion(id_opcion, opcion_texto):
    """Actualiza el texto de una opción."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE OPCIONES SET opcion = %s WHERE id_opcion = %s"
            cursor.execute(sql, (opcion_texto, id_opcion))
        conexion.commit()
    finally:
        conexion.close()


def eliminar_opcion(id_opcion):
    """Elimina una opción."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM OPCIONES WHERE id_opcion = %s", (id_opcion,))
        conexion.commit()
    finally:
        conexion.close()