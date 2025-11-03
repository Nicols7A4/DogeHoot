# game_events.py, url_for
from flask import session, url_for, request
from flask_socketio import join_room, leave_room, emit
from main import socketio, app # Importamos app para usar 'with app.app_context()'
import time
import eventlet # Necesario para los temporizadores
import random

# Importamos controladores
from controladores import controlador_partidas as ctrl_partidas
from controladores import preguntas_opciones as cpo 
from controladores import usuarios as ctrl_usuarios # Para actualizar puntos al final
from controladores import controlador_recompensas as c_rec

# ✅ IMPORTAR el diccionario compartido de ajax_game.py
from ajax_game import partidas_en_juego

# --- FUNCIONES AUXILIARES ---
def obtener_estado_lobby(pin):
    return partidas_en_juego.get(pin, {"participantes_sin_grupo": [], "grupos": [], "modalidad_grupal": False})

def calcular_puntos(tiempo_restante, tiempo_total):
    """Calcula puntos basados en la rapidez (ejemplo simple)."""
    if tiempo_restante <= 0: return 0
    # Más puntos cuanto más rápido (hasta 1000 base + 1000 extra)
    base = 1000
    bonus = int(1000 * (tiempo_restante / tiempo_total))
    return base + bonus

# --- EVENTOS DE SOCKET.IO ---

@socketio.on('iniciar_panel_anfitrion')
def al_iniciar_panel(data):
    pin = data.get('pin')
    if not pin: return
    join_room(pin)
    
    if pin not in partidas_en_juego:
        partida_db = ctrl_partidas.obtener_partida_por_pin(pin)
        if not partida_db: return

        grupos = []
        if partida_db['modalidad']:
            for i in range(partida_db.get('cant_grupos', 2)):
                grupos.append({
                    "numero": i + 1,
                    "nombre": f"Grupo {i + 1}", 
                    "miembros": [], 
                    "puntaje": 0, 
                    "respondio_pregunta": False # Flag para lógica grupal
                })

        partidas_en_juego[pin] = {
            "id_partida": partida_db['id_partida'],
            "id_cuestionario": partida_db['id_cuestionario'],
            "modalidad_grupal": partida_db['modalidad'],
            "estado": 'E', # Espera
            "pregunta_actual_index": -1,
            "preguntas_data": cpo.obtener_preguntas_por_cuestionario(partida_db['id_cuestionario']),
            "participantes": {}, # { 'nombre_usuario': {'grupo': 'Grupo 1', 'puntaje': 0} }
            "grupos": grupos,
            "participantes_sin_grupo": []
        }
    
    # emit('actualizar_estado_lobby', obtener_estado_lobby(pin))
    socketio.emit('actualizar_estado_lobby', obtener_estado_lobby(pin), room=pin, namespace='/')
    

# game_events.py
@socketio.on('unirse_como_jugador')
def al_unirse_jugador(data):
    pin = data.get('pin')
    nombre_usuario = session.get('nombre_usuario', f"Invitado_{random.randint(100,999)}")
    id_usuario = session.get('user_id')

    if not pin: return
    join_room(pin)

    # --- VALIDACIÓN: Verificar que la partida no esté finalizada ---
    partida_db = ctrl_partidas.obtener_partida_por_pin(pin)
    if not partida_db:
        socketio.emit('error_partida', {
            'mensaje': 'El código de sesión no es válido.'
        }, room=request.sid)
        return
    
    if partida_db.get('estado') == 'FINALIZADA':
        socketio.emit('error_partida', {
            'mensaje': 'Esta partida ya ha finalizado. No puedes unirte.'
        }, room=request.sid)
        return

    # Si la partida no está en memoria (jugador llegó antes), la cargamos de la BD
    if pin not in partidas_en_juego:
        # Inicializamos la partida en memoria (igual que en 'al_iniciar_panel')
        grupos = []
        if partida_db['modalidad']:
            for i in range(partida_db.get('cant_grupos', 2)):
                grupos.append({
                    "numero": i + 1,
                    "nombre": f"Grupo {i + 1}", 
                    "miembros": [], 
                    "puntaje": 0, 
                    "respondio_pregunta": False
                })

        partidas_en_juego[pin] = {
            "id_partida": partida_db['id_partida'],
            "id_cuestionario": partida_db['id_cuestionario'],
            "modalidad_grupal": partida_db['modalidad'],
            "estado": 'E',
            "pregunta_actual_index": -1,
            "preguntas_data": cpo.obtener_preguntas_por_cuestionario(partida_db['id_cuestionario']),
            "participantes": {},
            "grupos": grupos,
            "participantes_sin_grupo": []
        }

    partida = partidas_en_juego[pin]
    
    # --- VALIDACIÓN: Verificar si el id_usuario ya existe en la partida ---
    if id_usuario:  # Solo validar si el usuario está logueado
        for participante_nombre, participante_data in partida['participantes'].items():
            if participante_data.get('id_usuario') == id_usuario:
                # El usuario ya está en la partida, no lo agregamos de nuevo
                # Solo actualizamos su sesión/room
                socketio.emit('ya_en_partida', {
                    'mensaje': 'Ya estás en esta partida.',
                    'nombre': participante_nombre
                }, room=request.sid)
                return
    
    # El resto de la lógica para añadir al jugador no cambia...
    jugador_ya_existe = nombre_usuario in partida['participantes']
    if not jugador_ya_existe:
        partida['participantes'][nombre_usuario] = {
            'grupo': None, 
            'grupo_numero': 0, 
            'puntaje': 0, 
            'id_usuario': id_usuario,
            'respondio_pregunta': False  # ✅ Flag para rastrear si respondió esta pregunta
        }
        if partida['modalidad_grupal']:
            partida['participantes_sin_grupo'].append(nombre_usuario)
        else:
             if not partida['grupos']: partida['grupos'].append({'numero': 0, 'nombre':'Individual', 'miembros':[], 'puntaje':0, 'respondio_pregunta':False})
             partida['grupos'][0]['miembros'].append(nombre_usuario)

    
    # socketio.emit('actualizar_estado_lobby', partida, room=pin, namespace='/')
    partida = partidas_en_juego.get(pin)
    if not partida: return # Seguridad por si algo falló

    # Si el juego ha sido INICIADO ('J') Y esta es la pregunta inicial (-1)
    if partida['estado'] == 'J' and partida['pregunta_actual_index'] == -1:
        
        # Usamos un flag para asegurarnos de que esto solo se ejecute UNA VEZ
        if not partida.get('primera_pregunta_enviada', False):
            partida['primera_pregunta_enviada'] = True # Marcar como enviado
            
            # Damos un respiro (1-2 seg) para que el resto de jugadores
            # también terminen de cargar la página y unirse a la sala.
            eventlet.sleep(2) 
            
            # Ahora sí, enviamos la primera pregunta a todos en la sala.
            enviar_siguiente_pregunta(pin)
    
    # Notificar al lobby (si el juego aún está en 'E')
    elif partida['estado'] == 'E':
        socketio.emit('actualizar_estado_lobby', partida, room=pin, namespace='/')
    

@socketio.on('seleccionar_grupo')
def al_seleccionar_grupo(data):
    pin = data.get('pin')
    nombre_grupo = data.get('nombre_grupo')
    nombre_usuario = session.get('nombre_usuario')

    if not all([pin, nombre_grupo, nombre_usuario]) or pin not in partidas_en_juego: return
    partida = partidas_en_juego[pin]
    if not partida['modalidad_grupal']: return # Solo en modo grupal

    # Quitar de donde estuviera
    if nombre_usuario in partida['participantes_sin_grupo']:
        partida['participantes_sin_grupo'].remove(nombre_usuario)
    for g in partida['grupos']:
        if nombre_usuario in g['miembros']:
            g['miembros'].remove(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo_numero'] = 0

    # Añadir al nuevo grupo
    for g in partida['grupos']:
        if g['nombre'] == nombre_grupo:
            g['miembros'].append(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo'] = nombre_grupo
            partida['participantes'][nombre_usuario]['grupo_numero'] = g.get('numero', 0)
            break
            
    # emit('actualizar_estado_lobby', partida, room=pin)
    socketio.emit('actualizar_estado_lobby', partida, room=pin, namespace='/')

# --- EVENTOS DEL JUEGO ---

# Reemplaza tu función 'al_iniciar_juego' con esta:
@socketio.on('iniciar_juego')
def al_iniciar_juego(data):
    pin = data.get('pin')
    if not pin or pin not in partidas_en_juego:
        return
    
    partida = partidas_en_juego[pin]
    if partida['estado'] != 'E':
        return

    # --- VALIDACIÓN: Verificar que el cuestionario tenga preguntas ---
    if not partida.get('preguntas_data') or len(partida['preguntas_data']) == 0:
        socketio.emit('error_juego', {
            'mensaje': 'Este cuestionario no tiene preguntas. No se puede iniciar el juego.'
        }, room=pin, namespace='/')
        return

    # --- BLOQUE DEL BUG ELIMINADO ---
    # Ya no forzamos a los jugadores a un grupo.
    if partida['modalidad_grupal'] and partida['participantes_sin_grupo']:
        print(f"Advertencia: {len(partida['participantes_sin_grupo'])} jugadores inician sin grupo.")
        # Opcional: podrías moverlos al grupo 1 aquí si prefieres,
        # pero es mejor que elijan en el lobby.

    partida['estado'] = 'J' # Marcamos como en Juego

    # --- CAMBIO CLAVE: Redirigir a los jugadores ---
    with app.app_context():
        url_juego = url_for('pagina_juego', pin=pin)
        socketio.emit('redirigir_a_juego', {'url': url_juego}, room=pin, namespace='/')

    # Damos un segundo para que los clientes redirijan
    # eventlet.sleep(1.5) 
    
    # Enviamos la primera pregunta
    # enviar_siguiente_pregunta(pin)


def enviar_siguiente_pregunta(pin):
    partida = partidas_en_juego.get(pin) # Usamos get para evitar error si la partida ya no existe
    if not partida or partida['estado'] != 'J': return

    partida['pregunta_actual_index'] += 1
    
    if partida['pregunta_actual_index'] >= len(partida['preguntas_data']):
        # Ya no hay más preguntas, finalizamos
        # La llamada a finalizar_juego ya usa app.app_context internamente si es necesario
        finalizar_juego(pin)
        return

    # Resetear flags de respuesta grupal (pero NO puntaje_anterior aquí)
    for grupo in partida.get('grupos', []):
        grupo['respondio_pregunta'] = False
    
    # También para participantes individuales
    if not partida.get('modalidad_grupal', False):
        for nombre, data in partida.get('participantes', {}).items():
            data['respondio_pregunta'] = False  # ✅ Resetear flag individual

    pregunta_actual_db = partida['preguntas_data'][partida['pregunta_actual_index']]
    id_pregunta = pregunta_actual_db['id_pregunta']
    
    opciones = cpo.obtener_opciones_por_pregunta(id_pregunta)
    
    pregunta_para_enviar = {
        'index': partida['pregunta_actual_index'],
        'texto': pregunta_actual_db['pregunta'],
        'tiempo': pregunta_actual_db['tiempo'],
        'opciones': [{'id': o['id_opcion'], 'texto': o['opcion']} for o in opciones],
        'adjunto': pregunta_actual_db.get('adjunto') # <-- AÑADIR ESTO
    }

    # ===== CAMBIO AQUÍ: Usamos socketio.emit con namespace =====
    socketio.emit('nueva_pregunta', pregunta_para_enviar, room=pin, namespace='/')
    
    # Iniciamos el temporizador en el servidor (sin cambios)
    eventlet.spawn(temporizador_pregunta, pin, pregunta_actual_db['tiempo'])

def temporizador_pregunta(pin, duracion):
    """Espera 'duracion' segundos y luego muestra los resultados."""
    eventlet.sleep(duracion)
    with app.app_context(): # Mantenemos el contexto aquí
        mostrar_resultados_pregunta(pin)

@socketio.on('enviar_respuesta')
def al_recibir_respuesta(data):
    pin = data.get('pin')
    id_opcion_elegida = data.get('id_opcion')
    tiempo_restante = data.get('tiempo_restante', 0)
    nombre_usuario = session.get('nombre_usuario')

    if not all([pin, id_opcion_elegida, nombre_usuario]) or pin not in partidas_en_juego: return
    
    partida = partidas_en_juego[pin]
    if partida['estado'] != 'J': return # Solo se aceptan respuestas durante el juego

    participante = partida['participantes'].get(nombre_usuario)
    if not participante: return

    # Verificamos si la opción es correcta (consultando la BD)
    opcion_db = cpo.obtener_opcion_por_id(id_opcion_elegida)
    if not opcion_db: return

    es_correcta = opcion_db['es_correcta_bool']
    pregunta_actual_db = partida['preguntas_data'][partida['pregunta_actual_index']]
    tiempo_total = pregunta_actual_db['tiempo']

    puntos = calcular_puntos(tiempo_restante, tiempo_total) if es_correcta else 0
    
    print(f"🎯 [RESPUESTA] Usuario '{nombre_usuario}' respondió. Correcta: {es_correcta}, Puntos: {puntos}")

    # --- LÓGICA GRUPAL ---
    if partida['modalidad_grupal']:
        nombre_grupo = participante['grupo']
        if not nombre_grupo: return # Jugador no asignado a grupo
        
        grupo_encontrado = None
        for g in partida['grupos']:
            if g['nombre'] == nombre_grupo:
                grupo_encontrado = g
                break
        
        if not grupo_encontrado or grupo_encontrado['respondio_pregunta']:
            return # Grupo no existe o ya respondió

        grupo_encontrado['puntaje'] += puntos
        grupo_encontrado['respondio_pregunta'] = True
        
        print(f"✅ [GRUPO] '{nombre_grupo}' marcado como respondido. Puntaje: {grupo_encontrado['puntaje']}")
        
        # Guardamos la respuesta en la BD (simplificado)
        # ctrl_partidas.guardar_respuesta_participante(...)

        # Avisamos al anfitrión (opcional)
        emit('respuesta_recibida', {'grupo': nombre_grupo}, room=pin) 

    else: # --- LÓGICA INDIVIDUAL ---
        participante['puntaje'] += puntos
        participante['respondio_pregunta'] = True  # ✅ Marcar que respondió
        
        print(f"✅ [INDIVIDUAL] '{nombre_usuario}' marcado como respondido. Puntaje: {participante['puntaje']}")
        # Guardamos la respuesta en la BD (simplificado)
        # ctrl_partidas.guardar_respuesta_participante(...)
        # Avisamos al anfitrión (opcional)
        socketio.emit('respuesta_recibida', {'jugador': nombre_usuario}, room=pin, namespace='/')
        # emit('respuesta_recibida', {'jugador': nombre_usuario}, room=pin)


# game_events.py
def mostrar_resultados_pregunta(pin):
    partida = partidas_en_juego.get(pin)
    if not partida or partida['estado'] != 'J': return

    pregunta_actual_db = partida['preguntas_data'][partida['pregunta_actual_index']]
    id_pregunta = pregunta_actual_db['id_pregunta']
    
    # Buscamos la opción correcta en la BD
    opciones = cpo.obtener_opciones_por_pregunta(id_pregunta)
    id_opcion_correcta = next((o['id_opcion'] for o in opciones if o['es_correcta_bool']), None)
    
    # Obtenemos el TEXTO de la respuesta correcta
    texto_opcion_correcta = "N/A"
    if id_opcion_correcta:
        for o in opciones:
            if o['id_opcion'] == id_opcion_correcta:
                texto_opcion_correcta = o['opcion']
                break

    # --- INICIALIZAR puntaje_anterior si es la primera pregunta ---
    if partida['modalidad_grupal']:
        for g in partida['grupos']:
            if 'puntaje_anterior' not in g:
                g['puntaje_anterior'] = 0
    else:
        for nombre, data in partida['participantes'].items():
            if 'puntaje_anterior' not in data:
                data['puntaje_anterior'] = 0

    # --- ¡AQUÍ ESTÁ LA LÓGICA DE RANKING QUE FALTABA! ---
    if partida['modalidad_grupal']:
        ranking = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        ranking_data = []
        for g in ranking:
            # Calcular puntos ganados en ESTA pregunta
            puntos_actuales = g['puntaje']
            # Buscar el puntaje anterior del grupo en el ranking previo (si existe)
            puntos_anteriores = g.get('puntaje_anterior', 0)
            puntos_ganados = puntos_actuales - puntos_anteriores
            
            respondio = g.get('respondio_pregunta', False)
            print(f"🔍 [BACKEND] Grupo '{g['nombre']}': puntaje={puntos_actuales}, puntos_ganados={puntos_ganados}, respondio={respondio}")
            
            ranking_data.append({
                'nombre': g['nombre'], 
                'puntaje': g['puntaje'],
                'puntos_ganados': puntos_ganados,  # ✅ Agregamos esto
                'respondio': respondio  # ✅ Agregamos esto
            })
            
            # Guardar el puntaje actual para la próxima pregunta
            g['puntaje_anterior'] = puntos_actuales
    else:
        # Lógica para ranking individual
        ranking_ordenado = sorted(partida['participantes'].values(), key=lambda p: p['puntaje'], reverse=True)
        ranking_data = []
        nombres_usados = set() # Para evitar duplicados si la lógica se complica
        
        for p_data in ranking_ordenado:
             for nombre, data in partida['participantes'].items():
                 if data == p_data and nombre not in nombres_usados:
                     # Calcular puntos ganados en ESTA pregunta
                     puntos_actuales = data['puntaje']
                     puntos_anteriores = data.get('puntaje_anterior', 0)
                     puntos_ganados = puntos_actuales - puntos_anteriores
                     
                     respondio = data.get('respondio_pregunta', False)
                     print(f"🔍 [BACKEND] Jugador '{nombre}': puntaje={puntos_actuales}, puntos_ganados={puntos_ganados}, respondio={respondio}")
                     
                     ranking_data.append({
                         'nombre': nombre, 
                         'puntaje': data['puntaje'],
                         'puntos_ganados': puntos_ganados,  # ✅ Agregamos esto
                         'respondio': respondio  # ✅ NUEVO: Flag individual
                     })
                     
                     # Guardar el puntaje actual para la próxima pregunta
                     data['puntaje_anterior'] = puntos_actuales
                     
                     nombres_usados.add(nombre)
                     break
    # --- FIN DE LA LÓGICA DE RANKING ---

    resultados = {
        'texto_opcion_correcta': texto_opcion_correcta, # Enviamos el texto
        'ranking': ranking_data
    }
    
    print(f"📤 [EMIT] Enviando resultados: {resultados}")
    socketio.emit('mostrar_resultados', resultados, room=pin, namespace='/')
    
    eventlet.spawn(esperar_y_siguiente, pin, 2)


def esperar_y_siguiente(pin, segundos):
    eventlet.sleep(segundos)
    with app.app_context(): # Mantenemos el contexto aquí
         enviar_siguiente_pregunta(pin)

def finalizar_juego(pin):
    partida = partidas_en_juego.get(pin)
    if not partida or partida['estado'] == 'F': 
        return
    
    partida['estado'] = 'F'

    nombres_usados = set() # Importante definir esto
    ranking_data = [] # Importante definir esto

    if partida['modalidad_grupal']:
        ranking_final = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        # Calcular monedas para cada grupo
        for i, grupo in enumerate(ranking_final, start=1):
            base_por_puesto = {1: 100, 2: 75, 3: 50}
            base = base_por_puesto.get(i, 20)
            extra = grupo['puntaje'] // 50
            monedas = base + extra
            ranking_data.append({
                'nombre': grupo['nombre'], 
                'puntaje': grupo['puntaje'],
                'monedas': monedas,
                'posicion': i
            })
        
        # --- LÓGICA DE GUARDADO GRUPAL (DESCOMENTADA) ---
        for grupo in ranking_final:
            for miembro_nombre in grupo['miembros']:
                participante_data = partida['participantes'].get(miembro_nombre)
                if participante_data and participante_data['id_usuario']:
                    # Asumiendo que quieres sumar el puntaje del GRUPO al usuario
                    ctrl_usuarios.sumar_puntos(participante_data['id_usuario'], grupo['puntaje']) 
                    print(f"Guardando puntaje {grupo['puntaje']} para usuario {participante_data['id_usuario']}")
    
    else: # Modo individual
        ranking_final = sorted(partida['participantes'].values(), key=lambda p: p['puntaje'], reverse=True)
        
        posicion = 1
        for p_data in ranking_final:
            for nombre, data in partida['participantes'].items():
                if data == p_data and nombre not in nombres_usados: 
                    # Calcular monedas para este jugador
                    base_por_puesto = {1: 100, 2: 75, 3: 50}
                    base = base_por_puesto.get(posicion, 20)
                    extra = data['puntaje'] // 50
                    monedas = base + extra
                    
                    print(f"DEBUG: Jugador {nombre} - Posición {posicion} - Puntaje {data['puntaje']} - Monedas {monedas}")
                    
                    ranking_data.append({
                        'nombre': nombre, 
                        'puntaje': data['puntaje'],
                        'monedas': monedas,
                        'posicion': posicion
                    })
                    
                    # --- LÓGICA DE GUARDADO INDIVIDUAL (DESCOMENTADA) ---
                    if data['id_usuario']:
                        ctrl_usuarios.sumar_puntos(data['id_usuario'], data['puntaje'])
                    
                    nombres_usados.add(nombre)
                    posicion += 1
                    break # Pasa al siguiente p_data

    # Marcamos la partida como finalizada en la BD
    # ⚠️ NOTA: finalizar_partida() YA otorga recompensas automáticamente, no llamar otorgar_recompensas() aquí
    ctrl_partidas.finalizar_partida(partida['id_partida'])

    print(f"DEBUG: Enviando ranking_data al cliente: {ranking_data}")

    socketio.emit('juego_finalizado', {'ranking': ranking_data}, room=pin, namespace='/')
    
    if pin in partidas_en_juego:
        del partidas_en_juego[pin]



