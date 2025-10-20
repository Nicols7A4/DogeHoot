# game_events.py
from flask import session
from flask_socketio import join_room, emit
from main import socketio
from controladores import controlador_partidas as ctrl_partidas

partidas_en_juego = {}

def obtener_estado_lobby(pin):
    """Función auxiliar para obtener el estado actual y asegurar que no haya errores."""
    return partidas_en_juego.get(pin, {"participantes_sin_grupo": [], "grupos": []})

@socketio.on('iniciar_panel_anfitrion')
def al_iniciar_panel(data):
    pin = data.get('pin')
    if not pin: return
    
    join_room(pin)
    
    # Si la partida no está en memoria, la creamos desde la BD
    if pin not in partidas_en_juego:
        partida_db = ctrl_partidas.obtener_partida_por_pin(pin)
        if not partida_db: return

        grupos = []
        # Si es grupal, creamos los grupos vacíos
        if partida_db['modalidad']:
            for i in range(partida_db.get('cant_grupos', 2)):
                grupos.append({"nombre": f"Grupo {i + 1}", "miembros": []})

        partidas_en_juego[pin] = {
            "modalidad_grupal": partida_db['modalidad'],
            "participantes_sin_grupo": [],
            "grupos": grupos
        }
    
    emit('actualizar_estado_lobby', obtener_estado_lobby(pin))

@socketio.on('unirse_como_jugador')
def al_unirse_jugador(data):
    pin = data.get('pin')
    nombre_usuario = session.get('nombre_usuario', 'Invitado')

    if not pin or pin not in partidas_en_juego: return

    join_room(pin)
    partida = partidas_en_juego[pin]

    # Verificamos si el jugador ya está en algún lado
    jugador_ya_existe = nombre_usuario in partida['participantes_sin_grupo'] or \
                      any(nombre_usuario in g['miembros'] for g in partida['grupos'])
    
    if not jugador_ya_existe:
        # Si la partida es individual o grupal, el jugador siempre entra primero como "sin asignar"
        partida['participantes_sin_grupo'].append(nombre_usuario)

    emit('actualizar_estado_lobby', partida, room=pin)

@socketio.on('seleccionar_grupo')
def al_seleccionar_grupo(data):
    pin = data.get('pin')
    nombre_grupo = data.get('nombre_grupo')
    nombre_usuario = session.get('nombre_usuario')

    if not all([pin, nombre_grupo, nombre_usuario]) or pin not in partidas_en_juego: return
    
    partida = partidas_en_juego[pin]
    
    # Quitar al jugador de donde estuviera antes
    if nombre_usuario in partida['participantes_sin_grupo']:
        partida['participantes_sin_grupo'].remove(nombre_usuario)
    for g in partida['grupos']:
        if nombre_usuario in g['miembros']:
            g['miembros'].remove(nombre_usuario)

    # Añadir al jugador al nuevo grupo
    for g in partida['grupos']:
        if g['nombre'] == nombre_grupo:
            g['miembros'].append(nombre_usuario)
            break
            
    emit('actualizar_estado_lobby', partida, room=pin)