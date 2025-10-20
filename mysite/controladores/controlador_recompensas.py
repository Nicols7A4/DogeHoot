from bd import obtener_conexion

# --- Cálculo de recompensa ---
def calcular_recompensa(posicion, puntaje):
    """Calcula la cantidad de monedas según posición y puntaje."""
    base_por_puesto = {1: 100, 2: 75, 3: 50}
    base = base_por_puesto.get(posicion, 20)  # 4° o más = 20 monedas
    extra = puntaje // 50  # cada 50 puntos = +1 moneda
    return base + extra

# --- Otorgar recompensas a los jugadores ---
def otorgar_recompensas(id_partida):
    conexion = obtener_conexion()
    cursor = conexion.cursor()


    try:
        # Obtener los participantes y sus puntajes
        cursor.execute("""
            SELECT id_usuario, puntaje
            FROM PARTICIPANTE
            WHERE id_partida = %s
            ORDER BY puntaje DESC
        """, (id_partida,))
        participantes = cursor.fetchall()

        if not participantes:
            print(f"No hay participantes en la partida {id_partida}")
            return False

        #  Repartir monedas según el orden
        for i, p in enumerate(participantes, start=1):
            recompensa = calcular_recompensa(i, p['puntaje'])
            cursor.execute("""
                UPDATE USUARIO
                SET monedas = COALESCE(monedas, 0) + %s
                WHERE id_usuario = %s
            """, (recompensa, p['id_usuario']))

        conexion.commit()
        print(f"Recompensas otorgadas a la partida {id_partida}")
        return True

    except Exception as e:
        conexion.rollback()
        print(f"Error otorgando recompensas: {e}")
        return False

    finally:
        cursor.close()
        conexion.close()
