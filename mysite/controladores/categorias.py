from bd import obtener_conexion

def obtener_todas():
    """Obtiene una lista de todas las categorías disponibles."""
    conexion = obtener_conexion()
    categorias = []
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_categoria, categoria FROM CATEGORIA ORDER BY categoria ASC")
            categorias = cursor.fetchall()
    finally:
        if conexion:
            conexion.close()
    return categorias