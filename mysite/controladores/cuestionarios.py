# controladores/cuestionarios.py

import base64
import os
import re
import time
from main import app
from bd import obtener_conexion
from datetime import datetime

def crear(titulo, descripcion, es_publico, id_usuario, id_categoria, id_cuestionario_original=None):
    """Crea un nuevo cuestionario en la base de datos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO CUESTIONARIO (titulo, descripcion, es_publico, fecha_hora_creacion, id_usuario, id_categoria, id_cuestionario_original, vigente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(sql, (titulo, descripcion, es_publico, datetime.now(), id_usuario, id_categoria, id_cuestionario_original))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()

def obtener_con_filtros(id_usuario=None, id_categoria=None, es_publico=None):
    """Obtiene una lista de cuestionarios aplicando filtros opcionales."""
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = "SELECT * FROM CUESTIONARIO WHERE vigente = TRUE"
            params = []

            if id_usuario:
                query += " AND id_usuario = %s"
                params.append(id_usuario)
            if id_categoria:
                query += " AND id_categoria = %s"
                params.append(id_categoria)
            if es_publico is not None:
                query += " AND es_publico = %s"
                params.append(es_publico)

            cursor.execute(query, tuple(params))
            cuestionarios = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return cuestionarios

def obtener_por_id(id_cuestionario):
    """Obtiene un único cuestionario por su ID."""
    conexion = obtener_conexion()
    cuestionario = None
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM CUESTIONARIO WHERE id_cuestionario = %s AND vigente = TRUE", (id_cuestionario,))
            cuestionario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return cuestionario



def obtener_completo_por_id(id_cuestionario):
    """
    Obtiene un cuestionario con todas sus preguntas y opciones anidadas.
    Devuelve un único diccionario completo.
    """
    conexion = obtener_conexion()
    cuestionario_dict = None
    try:
        with conexion.cursor() as cursor:
            # --- Paso 1: Obtener los datos principales del cuestionario ---
            sql_cuestionario = "SELECT * FROM CUESTIONARIO WHERE id_cuestionario = %s AND vigente = TRUE"
            cursor.execute(sql_cuestionario, (id_cuestionario,))
            cuestionario_dict = cursor.fetchone()

            # Si no se encuentra el cuestionario, no continuamos
            if not cuestionario_dict:
                return None

            # --- Paso 2: Obtener todas las preguntas de ese cuestionario ---
            sql_preguntas = "SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s ORDER BY num_pregunta ASC"
            cursor.execute(sql_preguntas, (id_cuestionario,))
            preguntas = cursor.fetchall()

            # --- Paso 3: Para cada pregunta, obtener sus opciones ---
            for pregunta in preguntas:
                sql_opciones = "SELECT * FROM OPCIONES WHERE id_pregunta = %s"
                cursor.execute(sql_opciones, (pregunta['id_pregunta'],))
                opciones = cursor.fetchall()
                # Añadimos la lista de opciones directamente al diccionario de la pregunta
                pregunta['opciones'] = opciones

            # --- Paso 4: Finalmente, añadimos la lista de preguntas completas al cuestionario ---
            cuestionario_dict['preguntas'] = preguntas

    finally:
        if conexion:
            conexion.close()

    return cuestionario_dict



def actualizar(id_cuestionario, titulo, descripcion, es_publico, id_categoria, vigente):
    """
    Actualiza la información de un cuestionario existente en la base de datos.
    No modifica el id_usuario ni la fecha de creación.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                UPDATE CUESTIONARIO SET
                    titulo = %s,
                    descripcion = %s,
                    es_publico = %s,
                    id_categoria = %s,
                    vigente = %s
                WHERE id_cuestionario = %s
            """
            cursor.execute(sql, (titulo, descripcion, es_publico, id_categoria, vigente, id_cuestionario))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()


def desactivar(id_cuestionario):
    """
    Realiza un "soft delete" marcando el cuestionario como no vigente.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Actualiza la columna 'vigente' a FALSE para el ID especificado
            sql = "UPDATE CUESTIONARIO SET vigente = FALSE WHERE id_cuestionario = %s"
            cursor.execute(sql, (id_cuestionario,))
        conexion.commit()
        # Devuelve el número de filas afectadas. Si es 0, el cuestionario no existía.
        return cursor.rowcount > 0
    finally:
        if conexion:
            conexion.close()




def _guardar_imagen_base64(id_cuestionario, id_pregunta, adjunto_str):
    """
    Procesa el campo 'adjunto'. Si es una cadena Base64, la guarda como archivo.
    Si ya es una ruta, la devuelve sin cambios. Si está vacío, devuelve None.
    """
    # Si no hay nada o no es una cadena, no hacemos nada
    if not isinstance(adjunto_str, str):
        return None

    # Si es una cadena Base64, la procesamos
    if adjunto_str.startswith('data:image'):
        try:
            header, encoded = adjunto_str.split(',', 1)
            match = re.search(r'data:image/(?P<ext>\w+);base64', header)
            ext = match.group('ext') if match else 'jpg'
            image_data = base64.b64decode(encoded)

            timestamp = int(time.time())
            filename = f"pregunta_{id_pregunta}_{timestamp}.{ext}"
            upload_folder = os.path.join(app.root_path, 'static', 'img', 'cuestionarios', f'c_{id_cuestionario}')
            os.makedirs(upload_folder, exist_ok=True)

            ruta_completa = os.path.join(upload_folder, filename)
            with open(ruta_completa, 'wb') as f:
                f.write(image_data)

            return f"img/cuestionarios/c_{id_cuestionario}/{filename}"
        except Exception as e:
            print(f"Error al guardar imagen Base64: {e}")
            return None

    # Si no es una cadena Base64, asumimos que es una ruta ya existente y la devolvemos tal cual
    return adjunto_str



def guardar_o_actualizar_completo(data):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # --- 1. Guardar o Actualizar el CUESTIONARIO principal ---
            if data.get('id_cuestionario'):  # Si tiene ID, es una ACTUALIZACIÓN
                id_cuestionario = data['id_cuestionario']

                sql_update_cuestionario = """
                    UPDATE CUESTIONARIO SET
                        titulo = %s, descripcion = %s, es_publico = %s, id_categoria = %s, vigente = TRUE
                    WHERE id_cuestionario = %s
                """
                cursor.execute(sql_update_cuestionario, (
                    data['titulo'], data['descripcion'], data['es_publico'], data['id_categoria'], id_cuestionario
                ))

                # Estrategia "Demoler y Reconstruir": Borramos las preguntas antiguas.
                # ON DELETE CASCADE se encargará de borrar las opciones automáticamente.
                cursor.execute("DELETE FROM PREGUNTAS WHERE id_cuestionario = %s", (id_cuestionario,))

            else:  # Si no tiene ID, es un NUEVO CUESTIONARIO
                sql_insert_cuestionario = """
                    INSERT INTO CUESTIONARIO (titulo, descripcion, es_publico, fecha_hora_creacion, id_usuario, id_categoria, id_cuestionario_original, vigente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """
                cursor.execute(sql_insert_cuestionario, (
                    data['titulo'], data['descripcion'], data['es_publico'],
                    datetime.now(), data['id_usuario'], data['id_categoria'],
                    data.get('id_cuestionario_original')
                ))
                id_cuestionario = cursor.lastrowid

            # --- 2. Reconstruir las PREGUNTAS y OPCIONES ---
            for index, pregunta_data in enumerate(data.get('preguntas', [])):
                # Insertamos la pregunta SIN la imagen primero
                sql_pregunta = """
                    INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql_pregunta, (
                    id_cuestionario, pregunta_data['pregunta'], index + 1,
                    pregunta_data['puntaje_base'], pregunta_data['tiempo']
                ))
                id_pregunta_nueva = cursor.lastrowid

                # Si la pregunta tiene una imagen (en Base64), la guardamos y actualizamos la fila
                ruta_img_final = _guardar_imagen_base64(id_cuestionario, id_pregunta_nueva, pregunta_data.get('adjunto'))

                # if pregunta_data.get('adjunto'):
                #     ruta_img_final = _guardar_imagen_base64(id_cuestionario, id_pregunta_nueva, pregunta_data['adjunto'])

                if ruta_img_final:
                    cursor.execute("UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s", (ruta_img_final, id_pregunta_nueva))

                # Insertamos sus opciones
                for opcion_data in pregunta_data.get('opciones', []):
                    sql_opcion = """
                        INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_opcion, (
                        id_pregunta_nueva, opcion_data['opcion'], opcion_data['es_correcta_bool'],
                        opcion_data.get('descripcion'), opcion_data.get('adjunto')
                    ))

        conexion.commit()
        return id_cuestionario

    except Exception as e:
        conexion.rollback()
        raise e
    finally:
        if conexion:
            conexion.close()

