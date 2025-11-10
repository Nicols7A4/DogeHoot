# controladores/usuarios.py
from bd import obtener_conexion
import random
import re
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def crear_usuario_pendiente(nombre_completo, nombre_usuario, correo, contrasena, tipo):
    """
    Crea un usuario con verificado=FALSE y le asigna un código de verificación.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # ===== ¡CORRECCIÓN AQUÍ! =====
            # 1. Verificar si el correo O el nombre de usuario ya existen
            sql_verificar = "SELECT id_usuario FROM USUARIO WHERE (correo = %s OR nombre_usuario = %s) AND vigente = TRUE"
            cursor.execute(sql_verificar, (correo, nombre_usuario)) # Ahora pasamos ambos valores
            if cursor.fetchone():
                return False, "El correo o nombre de usuario ya está en uso."

            # 2. Generar código y fecha de expiración
            codigo = str(random.randint(100000, 999999))
            expiracion = datetime.now() + timedelta(minutes=15)

            # 3. Insertar el nuevo usuario como NO verificado
            sql_insertar = """
                INSERT INTO USUARIO (nombre_completo, nombre_usuario, correo, contraseña, tipo, vigente, verificado, codigo_verificacion, expiracion_codigo)
                VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, %s, %s)
            """
            cursor.execute(sql_insertar, (nombre_completo, nombre_usuario, correo, contrasena, tipo, codigo, expiracion))

        conexion.commit()
        return True, codigo
    finally:
        if conexion:
            conexion.close()
        
def crear_usuario_t(nombre_completo, nombre_usuario, correo, contrasena, tipo,foto=None,puntos=0,monedas=0,id_skin_activa=None):
    """
    Crea un usuario con verificado=FALSE y le asigna un código de verificación.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # ===== ¡CORRECCIÓN AQUÍ! =====
            # 1. Verificar si el correo O el nombre de usuario ya existen
            sql_verificar = "SELECT id_usuario FROM USUARIO WHERE (correo = %s OR nombre_usuario = %s) AND vigente = TRUE"
            cursor.execute(sql_verificar, (correo, nombre_usuario)) # Ahora pasamos ambos valores
            if cursor.fetchone():
                return False, "El correo o nombre de usuario ya está en uso."

            # 2. Generar código y fecha de expiración
            # codigo = str(random.randint(100000, 999999))
            # expiracion = datetime.now() + timedelta(minutes=15)

            # 3. Insertar el nuevo usuario como NO verificado
            sql_insertar = """
                INSERT INTO USUARIO (nombre_completo, nombre_usuario, correo, contraseña, tipo, vigente, verificado,puntos,monedas)
                VALUES (%s, %s, %s, %s, %s, TRUE, TRUE,%s,%s)
            """
            cursor.execute(sql_insertar, (nombre_completo, nombre_usuario, correo, contrasena, tipo,puntos,monedas))

        conexion.commit()
        return True, "Usuario registrado"
    finally:
        if conexion:
            conexion.close()

def verificar_y_activar_usuario(correo, codigo):
    print(f"--- INICIANDO VERIFICACIÓN para correo: {correo}, código: {codigo} ---") # DEBUG
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id_usuario, codigo_verificacion, expiracion_codigo FROM USUARIO WHERE correo = %s AND verificado = FALSE"
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()

            if not usuario:
                print("DEBUG: No se encontró un usuario pendiente con ese correo.") # DEBUG
                return "Usuario no encontrado o ya ha sido verificado."

            print(f"DEBUG: Usuario pendiente encontrado: {usuario}") # DEBUG

            if usuario['expiracion_codigo'] < datetime.now():
                print("DEBUG: El código ha expirado.") # DEBUG
                return "El código de verificación ha expirado. Por favor, regístrate de nuevo."

            if usuario['codigo_verificacion'] != codigo:
                print("DEBUG: El código es incorrecto.") # DEBUG
                return "El código de verificación es incorrecto."

            # Si todo está bien, actualizamos
            print(f"DEBUG: Código correcto. Actualizando usuario ID: {usuario['id_usuario']}") # DEBUG
            sql_update = "UPDATE USUARIO SET verificado = TRUE, codigo_verificacion = NULL, expiracion_codigo = NULL, puntos = 0, monedas = 0 WHERE id_usuario = %s"
            filas_afectadas = cursor.execute(sql_update, (usuario['id_usuario'],))

            print(f"DEBUG: Filas afectadas por el UPDATE: {filas_afectadas}") # DEBUG

        conexion.commit()
        print("DEBUG: Commit realizado.") # DEBUG
        return "OK"
    except Exception as e:
        print(f"DEBUG: Ocurrió una excepción: {e}") # DEBUG
        # En caso de error, es importante deshacer para no dejar la BD en un estado inconsistente
        conexion.rollback()
        return 'F'
        #raise e
    finally:
        if conexion:
            conexion.close()

# --- NO CAMBIES LA FUNCIÓN validar_credenciales ---
def validar_credenciales(correo, contrasena):
    # ... esta función ya está bien ...
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM USUARIO WHERE correo = %s AND contraseña = %s AND vigente = TRUE AND verificado = TRUE"
            cursor.execute(sql, (correo, contrasena))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario


def regenerar_codigo(correo):
    """
    Busca un usuario no verificado, genera un nuevo código y actualiza la expiración.
    Devuelve (True, nuevo_codigo) o (False, "mensaje de error").
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Busca al usuario por correo que aún no está verificado
            sql = "SELECT id_usuario FROM USUARIO WHERE correo = %s AND verificado = FALSE"
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()

            if not usuario:
                return False, "No se encontró una cuenta pendiente de verificación para este correo."

            # Genera un nuevo código y una nueva fecha de expiración (15 minutos más)
            nuevo_codigo = str(random.randint(100000, 999999))
            nueva_expiracion = datetime.now() + timedelta(minutes=15)

            # Actualiza la base de datos con los nuevos datos
            sql_update = "UPDATE USUARIO SET codigo_verificacion = %s, expiracion_codigo = %s WHERE id_usuario = %s"
            cursor.execute(sql_update, (nuevo_codigo, nueva_expiracion, usuario['id_usuario']))

        conexion.commit()
        return True, nuevo_codigo
    finally:
        if conexion:
            conexion.close()

# ----

def esta_pendiente_de_verificacion(correo):
    """
    Verifica si un correo corresponde a un usuario registrado que
    aún no ha verificado su cuenta. Devuelve True si está pendiente, False si no.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # La consulta correcta busca un usuario que esté activo (vigente) pero no verificado.
            sql = "SELECT id_usuario FROM USUARIO WHERE correo = %s AND vigente = TRUE AND verificado = FALSE"
            cursor.execute(sql, (correo,))
            usuario_pendiente = cursor.fetchone()

            # Si fetchone() encuentra un usuario, devuelve True; si no, devuelve False.
            if usuario_pendiente:
                return True
            else:
                return False
    finally:
        if conexion:
            conexion.close()

    # Este return es por si algo muy raro pasa y la conexión falla antes del 'try'.
    # En la práctica, casi nunca se llega aquí.
    return False

# ----



def crear_usuario(nombre_completo, nombre_usuario, correo, contrasena, tipo='E'):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 1. Verificar si el correo o nombre de usuario ya existen
            sql_verificar = "SELECT id_usuario FROM USUARIO WHERE correo = %s OR nombre_usuario = %s"
            cursor.execute(sql_verificar, (correo, nombre_usuario))
            if cursor.fetchone():
                return False, "El correo o nombre de usuario ya está en uso."

            # 2. Insertar el nuevo usuario con los valores por defecto
            sql_insertar = """
                INSERT INTO USUARIO (nombre_completo, nombre_usuario, correo, contraseña, tipo, puntos, monedas, vigente)
                VALUES (%s, %s, %s, %s, %s, 0, 0, TRUE)
            """
            cursor.execute(sql_insertar, (nombre_completo, nombre_usuario, correo, contrasena, tipo))

        conexion.commit()
        return True, "¡Te has registrado con éxito! Ahora puedes iniciar sesión."
    finally:
        if conexion:
            conexion.close()


def obtener_todos():
    conexion = obtener_conexion()
    usuarios = []
    try:
        with conexion.cursor() as cursor:
            # Se omite la columna 'contraseña' para no exponerla
            cursor.execute("SELECT id_usuario, nombre_completo, nombre_usuario, correo, tipo, puntos, monedas, vigente FROM USUARIO WHERE vigente = TRUE")
            usuarios = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return usuarios


def obtener_por_id(id_usuario):
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT u.id_usuario, u.nombre_completo, u.nombre_usuario, u.correo, u.contraseña,
                       u.tipo, u.puntos, u.monedas, u.vigente, u.id_skin_activa, s.ruta AS skin_ruta, u.foto
                FROM USUARIO u
                LEFT JOIN SKINS s ON u.id_skin_activa = s.id_skin
                WHERE u.id_usuario = %s
            """
            cursor.execute(sql, (id_usuario,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario

def obtener_por_correo(correo):
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT u.id_usuario, u.nombre_completo, u.nombre_usuario, u.correo, u.contraseña,
                       u.tipo, u.puntos, u.monedas, u.vigente, u.id_skin_activa, s.ruta AS skin_ruta, u.foto
                FROM USUARIO u
                LEFT JOIN SKINS s ON u.id_skin_activa = s.id_skin
                WHERE u.correo = %s
            """
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario

def obtener_por_id_auth(id_usuario):
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = """
               SELECT *
                FROM USUARIO 
                WHERE id_usuario = %s
            """
            cursor.execute(sql, (id_usuario,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario


def obtener_por_correo_auth(correo):
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT *
                FROM USUARIO 
                WHERE correo = %s
            """
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario



def actualizar(id_usuario, nombre_completo, nombre_usuario, correo, tipo, puntos, monedas, vigente):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                UPDATE USUARIO SET
                    nombre_completo = %s,
                    nombre_usuario = %s,
                    correo = %s,
                    tipo = %s,
                    puntos = %s,
                    monedas = %s,
                    vigente = %s
                WHERE id_usuario = %s
            """
            cursor.execute(sql, (nombre_completo, nombre_usuario, correo, tipo, puntos, monedas, vigente, id_usuario))
        conexion.commit()
    finally:
        if conexion:
            conexion.close()


# def actualizar_perfil(id_usuario, nombre_completo, nombre_usuario):
#     """
#     Actualiza únicamente el nombre completo y el nombre de usuario del perfil.
#     """
#     conexion = obtener_conexion()
#     try:
#         with conexion.cursor() as cursor:
#             # Validar que el nuevo nombre de usuario no esté ya en uso por OTRA persona
#             sql_check = "SELECT id_usuario FROM USUARIO WHERE nombre_usuario = %s AND id_usuario != %s AND vigente = 1"
#             cursor.execute(sql_check, (nombre_usuario, id_usuario))
#             if cursor.fetchone():
#                 return False, "Ese nombre de usuario ya está en uso."

#             # Si está libre, actualizamos
#             sql_update = """
#                 UPDATE USUARIO SET
#                     nombre_completo = %s,
#                     nombre_usuario = %s
#                 WHERE id_usuario = %s
#             """
#             cursor.execute(sql_update, (nombre_completo, nombre_usuario, id_usuario))
#         conexion.commit()
#         return True, "Perfil actualizado."
#     except Exception as e:
#         conexion.rollback()
#         return False, str(e)
#     finally:
#         if conexion:
#             conexion.close()

def actualizar_perfil(id_usuario, nombre_completo, nombre_usuario):
    """
    Actualiza únicamente el nombre completo y el nombre de usuario del perfil,
    solo si el usuario está vigente.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Validar que el nuevo nombre de usuario no esté ya en uso por OTRA persona
            sql_check = """
                SELECT id_usuario 
                FROM USUARIO 
                WHERE nombre_usuario = %s AND id_usuario != %s AND vigente = 1
            """
            cursor.execute(sql_check, (nombre_usuario, id_usuario))
            if cursor.fetchone():
                return False, "Ese nombre de usuario ya está en uso."

            # Actualizar solo si el usuario está vigente
            sql_update = """
                UPDATE USUARIO
                SET nombre_completo = %s,
                    nombre_usuario  = %s
                WHERE id_usuario = %s
                AND vigente = 1
            """
            cursor.execute(sql_update, (nombre_completo, nombre_usuario, id_usuario))

        conexion.commit()

        if cursor.rowcount == 0:
            # No se actualizó: o no existe el usuario o no está vigente
            return False, "No se pudo actualizar: usuario no encontrado o no vigente."

        return True, "Perfil actualizado."
    except Exception as e:
        if conexion:
            conexion.rollback()
        return False, str(e)
    finally:
        if conexion:
            conexion.close()


def actualizar_contrasena(id_usuario: int, antigua: str, nueva: str):
    """
    Cambia solo la contraseña de un usuario.
    Valida que la contraseña actual coincida y luego actualiza.
    Devuelve (ok: bool, msg: str).
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as c:
            # Verificar existencia y contraseña actual
            c.execute("SELECT 1 FROM USUARIO WHERE id_usuario=%s AND vigente=TRUE", (id_usuario,))
            if not c.fetchone():
                return False, "Usuario no encontrado."

            c.execute("SELECT 1 FROM USUARIO WHERE id_usuario=%s AND contraseña=%s LIMIT 1", (id_usuario, antigua))
            if not c.fetchone():
                return False, "La contraseña actual es incorrecta."

            # Actualizar a la nueva
            c.execute("UPDATE USUARIO SET contraseña=%s WHERE id_usuario=%s", (nueva, id_usuario))

        conexion.commit()
        return True, "OK"
    except Exception as e:
        try: conexion.rollback()
        except: pass
        return False, str(e)
    finally:
        if conexion:
            conexion.close()


def desactivar(id_usuario):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE USUARIO SET vigente = FALSE WHERE id_usuario = %s",
                (id_usuario,)
            )
            actualizado = cursor.rowcount  # 1 si actualizó, 0 si no
        conexion.commit()
        return actualizado == 1
    finally:
        if conexion:
            conexion.close()

def actualizar_skin(id_usuario, id_skin):
    """
    Actualiza la skin activa de un usuario.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE USUARIO SET skin_activa = %s WHERE id_usuario = %s"
            cursor.execute(sql, (id_skin, id_usuario))
        conexion.commit()
        return True, "Skin actualizada correctamente."
    except Exception as e:
        try: conexion.rollback()
        except: pass
        return False, str(e)
    finally:
        if conexion:
            conexion.close()

def generar_token_restablecimiento(id_usuario):
    """
    Genera un token seguro y temporal que contiene el ID del usuario.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(id_usuario, salt='password-reset-salt')

def verificar_token_restablecimiento(token, max_age_secs=900): # 15 minutos
    """
    Verifica el token. Si es válido y no ha expirado, devuelve el id_usuario.
    Si no, devuelve None.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        id_usuario = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=max_age_secs
        )
    except Exception:
        return None
    return id_usuario

def obtener_por_correo_sin_filtros(correo):
    """
    Devuelve el registro del usuario por correo, sin filtrar por vigente/verificado.
    Así podemos decidir en la ruta qué mensaje dar.
    """
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM USUARIO WHERE correo = %s"
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario

def obtener_por_correo(correo):
    """
    Busca un usuario por su dirección de correo electrónico.
    """
    conexion = obtener_conexion()
    usuario = None
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM USUARIO WHERE correo = %s AND vigente = TRUE AND verificado = 1"
            cursor.execute(sql, (correo,))
            usuario = cursor.fetchone()
    finally:
        if conexion:
            conexion.close()
    return usuario

def actualizar_contrasena(id_usuario, nueva_contrasena):
    """
    Actualiza la contraseña (en texto plano) de un usuario por su ID.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE USUARIO SET contraseña = %s WHERE id_usuario = %s"
            cursor.execute(sql, (nueva_contrasena, id_usuario))
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar contraseña: {e}")
        conexion.rollback()
        return False
    finally:
        if conexion:
            conexion.close()


def contrasena_cumple_politica(contrasena: str) -> bool:
    # Validate password according to the registration rules used on sign-up.
    if not contrasena:
        return False
    if len(contrasena) < 8:
        return False
    if not re.search(r'[a-z]', contrasena):
        return False
    if not re.search(r'[A-Z]', contrasena):
        return False
    if not re.search(r'\d', contrasena):
        return False
    if not re.search(r'[^A-Za-z0-9\s]', contrasena):
        return False
    return True

def correo_activo(correo: str, require_verificado: bool = False) -> bool:
    """
    Verifica si el correo pertenece a un usuario activo (vigente=TRUE).
    Si require_verificado=True, también exige verificado=TRUE.

    Returns:
        bool: True si cumple las condiciones, False en caso contrario.
    """
    if not correo:
        return False

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            correo_norm = correo.strip()

            base_sql = """
                SELECT 1
                FROM USUARIO
                WHERE LOWER(correo) = LOWER(%s)
                  AND vigente = TRUE
            """
            if require_verificado:
                base_sql += " AND verificado = TRUE"

            cursor.execute(base_sql, (correo_norm,))
            return cursor.fetchone() is not None
    except Exception:
        # Ante cualquier error, comportarse de forma segura: retornar False
        return False
    finally:
        if conexion:
            conexion.close()








def sumar_puntos(id_usuario, puntos_a_sumar):
    """
    Suma una cantidad de puntos al total de un usuario.
    """
    if not id_usuario or puntos_a_sumar == 0:
        return False # No hacemos nada si no hay usuario o puntos
        
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # Usamos UPDATE ... SET puntos = puntos + %s para sumar de forma segura
            sql = "UPDATE USUARIO SET puntos = puntos + %s WHERE id_usuario = %s"
            cursor.execute(sql, (puntos_a_sumar, id_usuario))
        
        conexion.commit()
        print(f"Se sumaron {puntos_a_sumar} puntos al usuario {id_usuario}")
        return True
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al sumar puntos al usuario {id_usuario}: {e}")
        return False
    finally:
        if conexion:
            conexion.close()

