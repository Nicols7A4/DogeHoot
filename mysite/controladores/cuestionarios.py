# controladores/cuestionarios.py

import base64
import os
import re
import time
# TEST con from main import app para Excel
# from main import app
from flask import current_app
#
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

# TEST para Excel
def crear_solo_cuestionario(titulo, descripcion, es_publico, fecha_hora_creacion, id_usuario, id_categoria, vigente, id_cuestionario_original=None):
    """
    Crea un nuevo registro de CUESTIONARIO (solo los datos básicos)
    y DEVUELVE el nuevo id_cuestionario.
    Usado por el endpoint /api/cuestionarios/guardar-basico.
    """
    conexion = obtener_conexion()
    nuevo_id = None
    try:
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO CUESTIONARIO
                (titulo, descripcion, es_publico, fecha_hora_creacion, id_usuario, id_categoria, id_cuestionario_original, vigente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                titulo, descripcion, es_publico,
                fecha_hora_creacion, id_usuario, id_categoria,
                id_cuestionario_original, vigente
            ))
            nuevo_id = cursor.lastrowid # ¡Obtenemos el ID de la fila recién insertada!
        conexion.commit()
    except Exception as e:
        print(f"Error en crear_solo_cuestionario: {e}")
        if conexion:
            conexion.rollback() # Deshacer cambios si hay un error
        raise e # Relanzar la excepción para que el API la capture
    finally:
        if conexion:
            conexion.close()
    return nuevo_id

def obtener_cuestionarios_todos():
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = "SELECT * FROM CUESTIONARIO;"
            cursor.execute(query)
            cuestionarios = cursor.fetchall()
    finally:
        if conexion: conexion.close()
    return cuestionarios

def obtener_cuestionario_por_id(id):
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = "SELECT * FROM CUESTIONARIO WHERE id_cuestionario = %s;"
            cursor.execute(query, (id))
            cuestionarios = cursor.fetchone()
    finally:
        if conexion: conexion.close()
    return cuestionarios

def obtener_con_filtros(id_usuario=None, id_categoria=None, es_publico=None):
    """Obtiene una lista de cuestionarios aplicando filtros opcionales."""
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = "SELECT * FROM CUESTIONARIO WHERE vigente = TRUE"
            query = """
                SELECT *
                FROM CUESTIONARIO CU
                JOIN CATEGORIA CA ON CA.id_categoria = CU.id_categoria
                WHERE CU.vigente = TRUE
                """
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

            query += " ORDER BY CU.fecha_hora_creacion DESC"

            cursor.execute(query, tuple(params))
            cuestionarios = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return cuestionarios


def obtener_mas_jugados(limite=9, excluir_usuario=None):
    """
    Obtiene los cuestionarios más jugados basado en el número de partidas.
    
    Args:
        limite: Número máximo de cuestionarios a devolver
        excluir_usuario: ID del usuario cuyos cuestionarios se excluirán
    
    Returns:
        Lista de cuestionarios ordenados por popularidad
    """
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = """
                SELECT CU.*, CA.categoria, U.nombre_usuario, COUNT(P.id_partida) as num_partidas
                FROM CUESTIONARIO CU
                JOIN CATEGORIA CA ON CA.id_categoria = CU.id_categoria
                JOIN USUARIO U ON U.id_usuario = CU.id_usuario
                LEFT JOIN PARTIDA P ON P.id_cuestionario = CU.id_cuestionario
                WHERE CU.vigente = TRUE AND CU.es_publico = 1
            """
            params = []

            if excluir_usuario:
                query += " AND CU.id_usuario != %s"
                params.append(excluir_usuario)

            query += """
                GROUP BY CU.id_cuestionario
                ORDER BY num_partidas DESC, CU.fecha_hora_creacion DESC
                LIMIT %s
            """
            params.append(limite)

            cursor.execute(query, tuple(params))
            cuestionarios = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return cuestionarios


def obtener_publicos(id_categoria=None, excluir_usuario=None):
    """
    Obtiene cuestionarios públicos de todos los profesores, opcionalmente filtrados por categoría.
    
    Args:
        id_categoria: Filtrar por categoría específica
        excluir_usuario: ID del usuario cuyos cuestionarios se excluirán
    """
    conexion = obtener_conexion()
    cuestionarios = []
    try:
        with conexion.cursor() as cursor:
            query = """
                SELECT CU.*, CA.categoria, U.nombre_usuario
                FROM CUESTIONARIO CU
                JOIN CATEGORIA CA ON CA.id_categoria = CU.id_categoria
                JOIN USUARIO U ON U.id_usuario = CU.id_usuario
                WHERE CU.vigente = TRUE AND CU.es_publico = 1
            """
            params = []

            if excluir_usuario:
                query += " AND CU.id_usuario != %s"
                params.append(excluir_usuario)

            if id_categoria:
                query += " AND CU.id_categoria = %s"
                params.append(id_categoria)

            query += " ORDER BY CU.fecha_hora_creacion DESC"

            cursor.execute(query, tuple(params) if params else ())
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

            # --- Paso 2: Obtener todas las preguntas de ese cuestionario (solo vigentes) ---
            sql_preguntas = "SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1 ORDER BY num_pregunta ASC"
            cursor.execute(sql_preguntas, (id_cuestionario,))
            preguntas = cursor.fetchall()

            # --- Paso 3: Para cada pregunta, obtener sus opciones (solo vigentes) ---
            for pregunta in preguntas:
                sql_opciones = "SELECT * FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1"
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
            # TEST para el Excel
            # ORIGINAL: upload_folder = os.path.join(app.root_path, 'static', 'img', 'cuestionarios', f'c_{id_cuestionario}')
            upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'cuestionarios', f'c_{id_cuestionario}')
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

                # ESTRATEGIA DE MERGE: Actualizar/Insertar/Soft-delete preguntas y opciones
                # Obtener IDs de preguntas actuales VIGENTES en BD
                cursor.execute("SELECT id_pregunta FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1", (id_cuestionario,))
                ids_preguntas_bd = {row['id_pregunta'] for row in cursor.fetchall()}
                ids_preguntas_data = set()

                # Procesar cada pregunta del formulario
                for index, pregunta_data in enumerate(data.get('preguntas', [])):
                    id_pregunta = pregunta_data.get('id_pregunta')
                    
                    # DEBUG: Log para ver qué está pasando
                    print(f"[DEBUG] Procesando pregunta {index + 1}: id_pregunta={id_pregunta}, pregunta={pregunta_data.get('pregunta')[:30]}...")
                    print(f"[DEBUG] ¿id_pregunta existe? {id_pregunta is not None}, ¿está en BD? {id_pregunta in ids_preguntas_bd if id_pregunta else 'N/A'}")

                    if id_pregunta and id_pregunta in ids_preguntas_bd:
                        # ACTUALIZAR pregunta existente
                        ids_preguntas_data.add(id_pregunta)
                        sql_update_pregunta = """
                            UPDATE PREGUNTAS SET
                                pregunta = %s, num_pregunta = %s, puntaje_base = %s, tiempo = %s
                            WHERE id_pregunta = %s
                        """
                        cursor.execute(sql_update_pregunta, (
                            pregunta_data['pregunta'], index + 1,
                            pregunta_data['puntaje_base'], pregunta_data['tiempo'], id_pregunta
                        ))

                        # Procesar imagen si cambió
                        ruta_img_final = _guardar_imagen_base64(id_cuestionario, id_pregunta, pregunta_data.get('adjunto'))
                        if ruta_img_final:
                            cursor.execute("UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s", (ruta_img_final, id_pregunta))
                        elif pregunta_data.get('adjunto') is None:
                            # Si adjunto es None, limpiamos la imagen
                            cursor.execute("UPDATE PREGUNTAS SET adjunto = NULL WHERE id_pregunta = %s", (id_pregunta,))

                        # MERGE de opciones para esta pregunta (solo vigentes)
                        cursor.execute("SELECT id_opcion FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1", (id_pregunta,))
                        ids_opciones_bd = {row['id_opcion'] for row in cursor.fetchall()}
                        ids_opciones_data = set()

                        for opcion_data in pregunta_data.get('opciones', []):
                            id_opcion = opcion_data.get('id_opcion')

                            if id_opcion and id_opcion in ids_opciones_bd:
                                # ACTUALIZAR opción existente
                                ids_opciones_data.add(id_opcion)
                                sql_update_opcion = """
                                    UPDATE OPCIONES SET
                                        opcion = %s, es_correcta_bool = %s, descripcion = %s, adjunto = %s
                                    WHERE id_opcion = %s
                                """
                                cursor.execute(sql_update_opcion, (
                                    opcion_data['opcion'], opcion_data['es_correcta_bool'],
                                    opcion_data.get('descripcion'), opcion_data.get('adjunto'), id_opcion
                                ))
                            else:
                                # INSERTAR nueva opción
                                sql_insert_opcion = """
                                    INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                                    VALUES (%s, %s, %s, %s, %s, 1)
                                """
                                cursor.execute(sql_insert_opcion, (
                                    id_pregunta, opcion_data['opcion'], opcion_data['es_correcta_bool'],
                                    opcion_data.get('descripcion'), opcion_data.get('adjunto')
                                ))

                        # SOFT DELETE de opciones que ya no existen
                        ids_opciones_eliminar = ids_opciones_bd - ids_opciones_data
                        for id_opcion_eliminar in ids_opciones_eliminar:
                            cursor.execute("UPDATE OPCIONES SET vigente = 0 WHERE id_opcion = %s", (id_opcion_eliminar,))
                            print(f"[DEBUG] Opción {id_opcion_eliminar} marcada como no vigente")

                    else:
                        # INSERTAR nueva pregunta
                        sql_insert_pregunta = """
                            INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
                            VALUES (%s, %s, %s, %s, %s, 1)
                        """
                        cursor.execute(sql_insert_pregunta, (
                            id_cuestionario, pregunta_data['pregunta'], index + 1,
                            pregunta_data['puntaje_base'], pregunta_data['tiempo']
                        ))
                        id_pregunta_nueva = cursor.lastrowid
                        ids_preguntas_data.add(id_pregunta_nueva)

                        # Guardar imagen si existe
                        ruta_img_final = _guardar_imagen_base64(id_cuestionario, id_pregunta_nueva, pregunta_data.get('adjunto'))
                        if ruta_img_final:
                            cursor.execute("UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s", (ruta_img_final, id_pregunta_nueva))

                        # Insertar opciones de la nueva pregunta
                        for opcion_data in pregunta_data.get('opciones', []):
                            sql_insert_opcion = """
                                INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                                VALUES (%s, %s, %s, %s, %s, 1)
                            """
                            cursor.execute(sql_insert_opcion, (
                                id_pregunta_nueva, opcion_data['opcion'], opcion_data['es_correcta_bool'],
                                opcion_data.get('descripcion'), opcion_data.get('adjunto')
                            ))

                # SOFT DELETE de preguntas que ya no existen
                ids_preguntas_eliminar = ids_preguntas_bd - ids_preguntas_data
                for id_pregunta_eliminar in ids_preguntas_eliminar:
                    print(f"[DEBUG] Marcando pregunta como no vigente: id={id_pregunta_eliminar}")
                    # Soft delete: marcar como no vigente
                    cursor.execute("UPDATE PREGUNTAS SET vigente = 0 WHERE id_pregunta = %s", (id_pregunta_eliminar,))
                    # También marcar sus opciones como no vigentes
                    cursor.execute("UPDATE OPCIONES SET vigente = 0 WHERE id_pregunta = %s", (id_pregunta_eliminar,))
                    print(f"[DEBUG] ✅ Pregunta {id_pregunta_eliminar} y sus opciones marcadas como no vigentes")
                
                print(f"[DEBUG] Total preguntas en BD después: {len(ids_preguntas_data)}")
                print(f"[DEBUG] Preguntas eliminadas: {len(ids_preguntas_eliminar)}")

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

                # --- Insertar preguntas y opciones para cuestionario nuevo ---
                for index, pregunta_data in enumerate(data.get('preguntas', [])):
                    sql_pregunta = """
                        INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
                        VALUES (%s, %s, %s, %s, %s, 1)
                    """
                    cursor.execute(sql_pregunta, (
                        id_cuestionario, pregunta_data['pregunta'], index + 1,
                        pregunta_data['puntaje_base'], pregunta_data['tiempo']
                    ))
                    id_pregunta_nueva = cursor.lastrowid

                    # Guardar imagen si existe
                    ruta_img_final = _guardar_imagen_base64(id_cuestionario, id_pregunta_nueva, pregunta_data.get('adjunto'))
                    if ruta_img_final:
                        cursor.execute("UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s", (ruta_img_final, id_pregunta_nueva))

                    # Insertar opciones
                    for opcion_data in pregunta_data.get('opciones', []):
                        sql_opcion = """
                            INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                            VALUES (%s, %s, %s, %s, %s, 1)
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


def clonar_cuestionario(id_cuestionario_original, id_usuario_nuevo):
    """
    Clona un cuestionario completo (con preguntas y opciones) para un nuevo usuario.
    El cuestionario clonado se crea como NO público (vigente=0) por defecto.
    
    Args:
        id_cuestionario_original: ID del cuestionario a clonar
        id_usuario_nuevo: ID del usuario que clonará el cuestionario
    
    Returns:
        tuple: (success: bool, result: int|str) 
               - Si tiene éxito: (True, id_cuestionario_nuevo)
               - Si falla: (False, mensaje_error)
    """
    print(f"[CONTROLADOR CLONAR] Iniciando clonación: cuestionario={id_cuestionario_original}, usuario={id_usuario_nuevo}")
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 1. Obtener datos del cuestionario original Y verificar que no sea el mismo creador
            cursor.execute("""
                SELECT titulo, descripcion, id_categoria, id_usuario
                FROM CUESTIONARIO
                WHERE id_cuestionario = %s
            """, (id_cuestionario_original,))
            cuestionario_orig = cursor.fetchone()
            
            print(f"[CONTROLADOR CLONAR] Cuestionario encontrado: {cuestionario_orig}")
            
            if not cuestionario_orig:
                print(f"[CONTROLADOR CLONAR] ERROR: Cuestionario no existe")
                return False, "El cuestionario no existe o no está disponible."
            
            # 2. Verificar que el usuario no sea el mismo creador
            if cuestionario_orig['id_usuario'] == id_usuario_nuevo:
                print(f"[CONTROLADOR CLONAR] ERROR: Usuario intenta clonar su propio cuestionario")
                return False, "No puedes clonar tu propio cuestionario. Ya lo tienes en tus cuestionarios."
            
            # 3. Verificar que el cuestionario original esté publicado
            cursor.execute("SELECT vigente FROM CUESTIONARIO WHERE id_cuestionario = %s", (id_cuestionario_original,))
            estado = cursor.fetchone()
            print(f"[CONTROLADOR CLONAR] Estado vigente: {estado}")
            if not estado or estado['vigente'] != 1:
                print(f"[CONTROLADOR CLONAR] ERROR: Cuestionario no está publicado")
                return False, "Solo se pueden clonar cuestionarios publicados."
            
            # 4. Crear el nuevo cuestionario (vigente pero NO público por defecto)
            nuevo_titulo = f"{cuestionario_orig['titulo']} (Copia)"
            print(f"[CONTROLADOR CLONAR] Creando nuevo cuestionario: {nuevo_titulo}")
            cursor.execute("""
                INSERT INTO CUESTIONARIO (titulo, descripcion, es_publico, fecha_hora_creacion, 
                                         id_usuario, id_categoria, id_cuestionario_original, vigente)
                VALUES (%s, %s, 0, NOW(), %s, %s, %s, 1)
            """, (nuevo_titulo, cuestionario_orig['descripcion'], id_usuario_nuevo, 
                  cuestionario_orig['id_categoria'], id_cuestionario_original))
            
            id_cuestionario_nuevo = cursor.lastrowid
            print(f"[CONTROLADOR CLONAR] Cuestionario creado con ID: {id_cuestionario_nuevo}")
            
            # 5. Clonar todas las preguntas
            cursor.execute("""
                SELECT id_pregunta, pregunta, num_pregunta, puntaje_base, tiempo, adjunto, vigente
                FROM PREGUNTAS
                WHERE id_cuestionario = %s AND vigente = 1
                ORDER BY num_pregunta
            """, (id_cuestionario_original,))
            preguntas = cursor.fetchall()
            
            print(f"[CONTROLADOR CLONAR] Clonando {len(preguntas)} preguntas")
            
            for pregunta in preguntas:
                # Insertar pregunta clonada
                cursor.execute("""
                    INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, adjunto, vigente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (id_cuestionario_nuevo, pregunta['pregunta'], pregunta['num_pregunta'],
                      pregunta['puntaje_base'], pregunta['tiempo'], pregunta['adjunto'], pregunta['vigente']))
                
                id_pregunta_nueva = cursor.lastrowid
                
                # 6. Clonar opciones de esta pregunta
                cursor.execute("""
                    SELECT opcion, es_correcta_bool, descripcion, adjunto, vigente
                    FROM OPCIONES
                    WHERE id_pregunta = %s AND vigente = 1
                    ORDER BY id_opcion
                """, (pregunta['id_pregunta'],))
                opciones = cursor.fetchall()
                
                for opcion in opciones:
                    cursor.execute("""
                        INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_pregunta_nueva, opcion['opcion'], opcion['es_correcta_bool'], 
                          opcion['descripcion'], opcion['adjunto'], opcion['vigente']))
        
        conexion.commit()
        print(f"[CONTROLADOR CLONAR] ✅ Clonación exitosa! ID nuevo: {id_cuestionario_nuevo}")
        return True, id_cuestionario_nuevo
        
    except Exception as e:
        conexion.rollback()
        print(f"[CONTROLADOR CLONAR] ❌ Error: {e}")
        return False, f"Error al clonar el cuestionario: {str(e)}"
    finally:
        if conexion:
            conexion.close()

