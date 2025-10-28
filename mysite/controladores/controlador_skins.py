from bd import obtener_conexion

# --- Obtener todas las skins disponibles ---
def obtener_todas():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM SKINS WHERE vigente = 1")
            return cursor.fetchall()
    finally:
        conexion.close()


# --- Obtener las skins que el usuario ya posee ---
def obtener_por_usuario(id_usuario):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT s.id_skin, s.ruta, s.vigente
                FROM SKINS s
                INNER JOIN INVENTARIO_SKINS i ON s.id_skin = i.id_skin
                WHERE i.id_usuario = %s
            """
            cursor.execute(sql, (id_usuario,))
            return cursor.fetchall()
    finally:
        conexion.close()


# --- Comprar una skin (canjear con monedas) ---
def comprar_skin(id_usuario, id_skin, costo):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Verificar monedas del usuario
            cursor.execute("SELECT monedas FROM USUARIO WHERE id_usuario = %s", (id_usuario,))
            row = cursor.fetchone()
            if not row:
                return False, "Usuario no encontrado."

            monedas_actuales = row['monedas'] or 0
            if monedas_actuales < costo:
                return False, "No tienes suficientes monedas para comprar esta skin."

            # Verificar si ya tiene la skin
            cursor.execute(
                "SELECT 1 FROM INVENTARIO_SKINS WHERE id_usuario = %s AND id_skin = %s",
                (id_usuario, id_skin)
            )
            if cursor.fetchone():
                return False, "Ya tienes esta skin."

            # Descontar monedas y registrar compra
            cursor.execute("UPDATE USUARIO SET monedas = monedas - %s WHERE id_usuario = %s", (costo, id_usuario))
            cursor.execute("INSERT INTO INVENTARIO_SKINS (id_usuario, id_skin) VALUES (%s, %s)", (id_usuario, id_skin))

        conexion.commit()
        return True, "¡Skin comprada exitosamente!"
    except Exception as e:
        conexion.rollback()
        return False, f"Error al comprar skin: {e}"
    finally:
        conexion.close()

def cambiar_skin_activa(id_usuario, id_skin):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Verificar si el usuario tiene la skin
            cursor.execute("""
                SELECT 1 FROM INVENTARIO_SKINS
                WHERE id_usuario = %s AND id_skin = %s
            """, (id_usuario, id_skin))
            if not cursor.fetchone():
                return False, "No posees esta skin."

            # Actualizar skin activa
            cursor.execute("""
                UPDATE USUARIO SET id_skin_activa = %s WHERE id_usuario = %s
            """, (id_skin, id_usuario))
        conexion.commit()
        return True, "Skin cambiada exitosamente."
    except Exception as e:
        conexion.rollback()
        return False, f"Error al cambiar skin: {e}"
    finally:
        conexion.close()

def quitar_skin_activa(id_usuario):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Quitar skin activa (poner NULL o valor por defecto)
            cursor.execute("""
                UPDATE USUARIO
                SET id_skin_activa = NULL
                WHERE id_usuario = %s
            """, (id_usuario,))
            conexion.commit()

        return True, "Has quitado tu skin actual."
    except Exception as e:
        print("Error al quitar skin activa:", e)
        traceback.print_exc()
        return False, "Error al quitar la skin."
    finally:
        conexion.close()

