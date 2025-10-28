from bd import obtener_conexion

# --- Cálculo de recompensa ---
def calcular_recompensa(posicion, puntaje):
    """Calcula la cantidad de monedas según posición y puntaje."""
    base_por_puesto = {1: 100, 2: 75, 3: 50}
    base = base_por_puesto.get(posicion, 20)  # 4° o más = 20 monedas
    extra = puntaje // 50  # cada 50 puntos = +1 moneda
    return base + extra

# --- Otorgar recompensas a los jugadores ---
def otorgar_recompensas(id_partida, ranking_data=None):
    """
    Otorga monedas a los jugadores según su posición y puntaje.
    Incluye protección contra llamadas duplicadas.
    
    Args:
        id_partida: ID de la partida
        ranking_data: Lista opcional de dict con 'id_usuario', 'puntaje' y 'posicion'
                     Si no se proporciona, se consulta de la BD (menos confiable)
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # ⚠️ PROTECCIÓN: Verificar si ya se otorgaron recompensas para esta partida
        cursor.execute("""
            SELECT recompensas_otorgadas
            FROM PARTIDA
            WHERE id_partida = %s
        """, (id_partida,))
        partida = cursor.fetchone()
        
        if not partida:
            print(f"ERROR: Partida {id_partida} no existe")
            return False
            
        # Si ya se otorgaron recompensas, no hacer nada
        if partida.get('recompensas_otorgadas', 0) == 1:
            print(f"⚠️ ADVERTENCIA: Las recompensas ya fueron otorgadas para la partida {id_partida}. Ignorando llamada duplicada.")
            return True  # Retornar True porque técnicamente ya están otorgadas

        # Si se proporciona ranking_data, usar eso (más confiable)
        if ranking_data:
            print(f"🎯 Usando ranking_data proporcionado para otorgar recompensas")
            for item in ranking_data:
                id_usuario = item.get('id_usuario')
                posicion = item.get('posicion')
                puntaje = item.get('puntaje')
                
                if not id_usuario:
                    continue
                    
                recompensa = calcular_recompensa(posicion, puntaje)
                print(f"  → Usuario {id_usuario}: Pos {posicion}, Puntaje {puntaje} = {recompensa} monedas")
                
                cursor.execute("""
                    UPDATE USUARIO
                    SET monedas = COALESCE(monedas, 0) + %s
                    WHERE id_usuario = %s
                """, (recompensa, id_usuario))
        else:
            # Fallback: Obtener los participantes de la BD (menos confiable)
            print(f"⚠️ Usando datos de BD (menos confiable) para otorgar recompensas")
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

            # Repartir monedas según el orden
            for i, p in enumerate(participantes, start=1):
                recompensa = calcular_recompensa(i, p['puntaje'])
                print(f"  → Usuario {p['id_usuario']}: Pos {i}, Puntaje {p['puntaje']} = {recompensa} monedas")
                cursor.execute("""
                    UPDATE USUARIO
                    SET monedas = COALESCE(monedas, 0) + %s
                    WHERE id_usuario = %s
                """, (recompensa, p['id_usuario']))

        # ⚠️ PROTECCIÓN: Marcar que las recompensas ya fueron otorgadas
        cursor.execute("""
            UPDATE PARTIDA
            SET recompensas_otorgadas = 1
            WHERE id_partida = %s
        """, (id_partida,))

        conexion.commit()
        print(f"✅ Recompensas otorgadas exitosamente a la partida {id_partida}")
        return True

    except Exception as e:
        conexion.rollback()
        print(f"❌ Error otorgando recompensas: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        cursor.close()
        conexion.close()
