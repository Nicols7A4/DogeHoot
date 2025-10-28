import time
from flask import session
import random

from controladores import controlador_partidas as ctrl_partidas
from controladores import preguntas_opciones as cpo
from controladores import usuarios as ctrl_usuarios


# Estado de partidas en memoria (similar a game_events)
partidas_en_juego = {}

RESULTS_DELAY_SECONDS = 4  # Tiempo de visualización del ranking/resultados (aumentado a 4 para mejor legibilidad)

def _calcular_puntos(tiempo_restante, tiempo_total):
    if tiempo_restante is None or tiempo_total is None:
        return 0
    if tiempo_restante <= 0:
        return 0
    base = 1000
    bonus = int(1000 * (tiempo_restante / float(tiempo_total)))
    return base + bonus


def _ensure_loaded(pin):
    if pin in partidas_en_juego:
        return partidas_en_juego[pin]

    partida_db = ctrl_partidas.obtener_partida_por_pin(pin)
    if not partida_db:
        return None

    # preguntas una sola vez
    preguntas = cpo.obtener_preguntas_por_cuestionario(partida_db['id_cuestionario']) or []

    # preparar grupos
    grupos = []
    if partida_db.get('modalidad'):  # True si es grupal
        n = int(partida_db.get('cant_grupos') or 2)
        for i in range(n):
            grupos.append({
                'numero': i + 1,
                'nombre': f"Grupo {i+1}",
                'miembros': [],
                'puntaje': 0,
                'respondio_pregunta': False,
            })

    partidas_en_juego[pin] = {
        'id_partida': partida_db['id_partida'],
        'id_cuestionario': partida_db['id_cuestionario'],
        'modalidad_grupal': bool(partida_db.get('modalidad')),
        'estado': 'E',                 # E=espera, J=jugando, F=finalizado
        'fase': 'lobby',               # lobby | question | results | final
        'pregunta_actual_index': -1,
        'preguntas_data': preguntas,   # usamos la lista ya cargada
        'participantes': {},           # nombre -> {grupo, grupo_numero, puntaje, id_usuario, ...}
        'grupos': grupos,
        'participantes_sin_grupo': [],
        # tiempos
        'question_started_at': None,
        'question_duration': None,
        'results_started_at': None,
        'ultimo_resultado': None,
        # para calcular puntos ganados por pregunta
        'puntajes_pregunta_anterior': {},  # {nombre: puntaje_anterior}
    }

    return partidas_en_juego[pin]



def get_lobby_state(pin):
    partida = partidas_en_juego.get(pin)
    if not partida:
        return {'participantes_sin_grupo': [], 'grupos': [], 'modalidad_grupal': False}
    
    # Incluir info de participantes sin grupo con foto y skin
    participantes_sin_grupo_info = []
    for nombre in partida['participantes_sin_grupo']:
        p_data = partida['participantes'].get(nombre, {})
        participantes_sin_grupo_info.append({
            'nombre': nombre,
            'foto': p_data.get('foto', 'img/ico.png'),
            'skin': p_data.get('skin')
        })
    
    # Incluir info de grupos con miembros y sus fotos/skins
    grupos_info = []
    for g in partida.get('grupos', []):
        miembros_info = []
        for nombre in g['miembros']:
            p_data = partida['participantes'].get(nombre, {})
            miembros_info.append({
                'nombre': nombre,
                'foto': p_data.get('foto', 'img/ico.png'),
                'skin': p_data.get('skin')
            })
        grupos_info.append({
            'nombre': g['nombre'],
            'miembros': miembros_info,
            'puntaje': g['puntaje'],
        })
    
    return {
        'modalidad_grupal': partida['modalidad_grupal'],
        'participantes_sin_grupo': participantes_sin_grupo_info,
        'grupos': grupos_info,
    }


def join_player(pin):
    partida = _ensure_loaded(pin)
    if not partida:
        return None

    nombre_usuario = session.get('nombre_usuario')
    if not nombre_usuario:
        # fallback invitado si no hubiera nombre en sesión
        import random
        nombre_usuario = f"Invitado_{random.randint(100,999)}"
    id_usuario = session.get('user_id')
    
    # Obtener foto y skin del usuario
    foto = 'img/ico.png'
    skin = None
    if id_usuario:
        user_data = ctrl_usuarios.obtener_por_id(id_usuario)
        if user_data:
            foto = user_data.get('foto') or 'img/ico.png'
            skin = user_data.get('skin_ruta')

    if nombre_usuario not in partida['participantes']:
        partida['participantes'][nombre_usuario] = {
            'grupo': None,
            'grupo_numero': 0,
            'puntaje': 0,
            'id_usuario': id_usuario,
            'foto': foto,
            'skin': skin
        }
        if partida['modalidad_grupal']:
            partida['participantes_sin_grupo'].append(nombre_usuario)
        else:
            if not partida['grupos']:
                partida['grupos'].append({'numero': 0, 'nombre': 'Individual', 'miembros': [], 'puntaje': 0, 'respondio_pregunta': False})
            partida['grupos'][0]['miembros'].append(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo'] = 'Individual'
            partida['participantes'][nombre_usuario]['grupo_numero'] = 0

    # Retornar información incluyendo el grupo
    return {
        'participante': partida['participantes'][nombre_usuario],
        'grupo': partida['participantes'][nombre_usuario].get('grupo'),
        'modalidad_grupal': partida['modalidad_grupal']
    }


def select_group(pin, nombre_grupo):
    partida = partidas_en_juego.get(pin)
    if not partida or not partida['modalidad_grupal']:
        return False

    nombre_usuario = session.get('nombre_usuario')
    if not nombre_usuario:
        return False

    if nombre_usuario in partida['participantes_sin_grupo']:
        partida['participantes_sin_grupo'].remove(nombre_usuario)
    for g in partida['grupos']:
        if nombre_usuario in g['miembros']:
            g['miembros'].remove(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo_numero'] = 0

    for g in partida['grupos']:
        if g['nombre'] == nombre_grupo:
            g['miembros'].append(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo'] = nombre_grupo
            partida['participantes'][nombre_usuario]['grupo_numero'] = g.get('numero', 0)
            return True
    return False


def remove_player(pin):
    """Remueve al jugador actual de la partida"""
    partida = partidas_en_juego.get(pin)
    if not partida:
        return False

    nombre_usuario = session.get('nombre_usuario')
    if not nombre_usuario:
        return False

    # Remover de participantes
    if nombre_usuario in partida['participantes']:
        del partida['participantes'][nombre_usuario]

    # Remover de la lista de sin grupo
    if nombre_usuario in partida['participantes_sin_grupo']:
        partida['participantes_sin_grupo'].remove(nombre_usuario)

    # Remover de los grupos
    for g in partida['grupos']:
        if nombre_usuario in g['miembros']:
            g['miembros'].remove(nombre_usuario)
            partida['participantes'][nombre_usuario]['grupo_numero'] = 0
            break

    return True


def _assign_unassigned_players_to_groups(partida):
    """Auto-asigna jugadores sin grupo a grupos aleatorios"""
    if not partida['modalidad_grupal']:
        return  # Solo para modal grupal
    
    participantes_sin_grupo = partida['participantes_sin_grupo']
    
    if not participantes_sin_grupo:
        return  # No hay sin asignar
    
    for nombre_usuario in participantes_sin_grupo:
        # Elige grupo aleatorio
        grupo_aleatorio = random.choice(partida['grupos'])
        
        # Asigna participante al grupo
        grupo_aleatorio['miembros'].append(nombre_usuario)
        partida['participantes'][nombre_usuario]['grupo'] = grupo_aleatorio['nombre']
        partida['participantes'][nombre_usuario]['grupo_numero'] = grupo_aleatorio.get('numero', 0)
        
        print(f"[AUTO-ASIGNAR] {nombre_usuario} → {grupo_aleatorio['nombre']}")
    
    # Limpia lista de sin grupo
    partida['participantes_sin_grupo'] = []


def start_game(pin):
    partida = partidas_en_juego.get(pin)
    if not partida or partida['estado'] != 'E':
        return False
    
    # Validar que haya al menos un participante
    if not partida['participantes']:
        return False
    
    _assign_unassigned_players_to_groups(partida)

    partida['estado'] = 'J'
    # arrancar en primera pregunta
    return _start_next_question(pin)


def _start_next_question(pin):
    partida = partidas_en_juego.get(pin)
    if not partida or partida['estado'] != 'J':
        return False

    # Guardar puntajes actuales como "puntajes de pregunta anterior"
    partida['puntajes_pregunta_anterior'] = {}
    if partida['modalidad_grupal']:
        for g in partida['grupos']:
            partida['puntajes_pregunta_anterior'][g['nombre']] = g['puntaje']
    else:
        for nombre, participante in partida['participantes'].items():
            partida['puntajes_pregunta_anterior'][nombre] = participante['puntaje']

    # siguiente índice
    partida['pregunta_actual_index'] += 1

    if partida['pregunta_actual_index'] >= len(partida['preguntas_data']):
        finalize_game(pin)
        return False

    # resetear flags grupales Y de respuesta por pregunta
    for g in partida.get('grupos', []):
        g['respondio_pregunta'] = False
    
    # Resetear flags de respuesta para modo individual
    for nombre, participante in partida['participantes'].items():
        participante['respondio_esta_pregunta'] = False

    pregunta = partida['preguntas_data'][partida['pregunta_actual_index']]
    partida['fase'] = 'question'
    partida['question_started_at'] = time.time()
    partida['question_duration'] = pregunta['tiempo']
    partida['results_started_at'] = None
    partida['ultimo_resultado'] = None
    return True


def _compute_question_payload(partida, nombre_usuario=None):
    pregunta = partida['preguntas_data'][partida['pregunta_actual_index']]
    opciones = cpo.obtener_opciones_por_pregunta(pregunta['id_pregunta'])
    
    # ⭐ DETECTAR SI MI GRUPO YA RESPONDIÓ (solo para modalidad grupal)
    grupo_respondio = False
    quien_respondio = None
    respuesta_texto = None
    
    if partida['modalidad_grupal'] and nombre_usuario:
        # Obtener mi grupo
        mi_participante = partida['participantes'].get(nombre_usuario)
        if mi_participante:
            mi_grupo_nombre = mi_participante.get('grupo')
            # Buscar si MI grupo respondió esta pregunta
            for g in partida['grupos']:
                if g['nombre'] == mi_grupo_nombre and g.get('respondio_pregunta', False):
                    grupo_respondio = True
                    # Encontrar quién respondió del MI grupo
                    for nombre, participante in partida['participantes'].items():
                        if participante.get('grupo') == mi_grupo_nombre and participante.get('respondio_esta_pregunta', False):
                            quien_respondio = nombre
                            # Encontrar el texto de la opción respondida
                            if participante.get('id_opcion_respondida'):
                                for op in opciones:
                                    if op['id_opcion'] == participante['id_opcion_respondida']:
                                        respuesta_texto = op['opcion']
                                        break
                            break
                    break
    
    return {
        'index': partida['pregunta_actual_index'],
        'texto': pregunta['pregunta'],
        'tiempo': pregunta['tiempo'],
        'opciones': [{'id': o['id_opcion'], 'texto': o['opcion']} for o in opciones],
        'adjunto': pregunta.get('adjunto'),
        'started_at': partida['question_started_at'],
        'server_time': time.time(),
        'servidor_ahora': time.time(),
        # ⭐ NUEVOS CAMPOS PARA MODALIDAD GRUPAL
        'grupo_respondio': grupo_respondio,
        'quien_respondio': quien_respondio,
        'respuesta_texto': respuesta_texto,
    }


def _compute_results(partida):
    # obtener texto de la opción correcta
    pregunta = partida['preguntas_data'][partida['pregunta_actual_index']]
    opciones = cpo.obtener_opciones_por_pregunta(pregunta['id_pregunta'])
    id_correcta = next((o['id_opcion'] for o in opciones if o['es_correcta_bool']), None)
    texto_correcta = 'N/A'
    if id_correcta:
        for o in opciones:
            if o['id_opcion'] == id_correcta:
                texto_correcta = o['opcion']
                break

    if partida['modalidad_grupal']:
        ranking = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        ranking_data = [{'nombre': g['nombre'], 'puntaje': g['puntaje']} for g in ranking]
    else:
        ranking_ordenado = sorted(partida['participantes'].values(), key=lambda p: p['puntaje'], reverse=True)
        ranking_data, usados = [], set()
        for p_data in ranking_ordenado:
            for nombre, data in partida['participantes'].items():
                if data == p_data and nombre not in usados:
                    ranking_data.append({'nombre': nombre, 'puntaje': data['puntaje']})
                    usados.add(nombre)
                    break

    # Obtener información de si el usuario actual respondió correctamente
    nombre_usuario = session.get('nombre_usuario')
    respondio_correcta = False
    respondio_pregunta = False
    
    if nombre_usuario and nombre_usuario in partida['participantes']:
        participante = partida['participantes'][nombre_usuario]
        respondio_pregunta = participante.get('respondio_esta_pregunta', False)
        # Si respondió, check si fue correcta
        if respondio_pregunta:
            respondio_correcta = participante.get('respuesta_correcta', False)

    return {
        'texto_opcion_correcta': texto_correcta,
        'ranking': ranking_data,
        'pregunta_numero': partida['pregunta_actual_index'] + 1,
        'respondio_correcta': respondio_correcta,
        'respondio_pregunta': respondio_pregunta,
    }


def _todos_han_respondido(partida):
    """Verifica si todos los participantes o grupos ya respondieron la pregunta actual"""
    if partida['modalidad_grupal']:
        # En modo grupal: verificar que todos los grupos con miembros hayan respondido
        for grupo in partida['grupos']:
            # Solo contar grupos que tienen miembros
            if len(grupo['miembros']) > 0:
                if not grupo.get('respondio_pregunta', False):
                    return False
        return True
    else:
        # En modo individual: verificar que todos los participantes hayan respondido
        for nombre, participante in partida['participantes'].items():
            if not participante.get('respondio_esta_pregunta', False):
                return False
        return True


def advance_state_if_needed(pin):
    partida = partidas_en_juego.get(pin)
    if not partida:
        return None

    now = time.time()
    
    # Avanzar de pregunta a resultados cuando se acaba el tiempo O cuando todos ya respondieron
    if partida['estado'] == 'J' and partida['fase'] == 'question':
        if partida['question_started_at'] is not None and partida['question_duration'] is not None:
            tiempo_agotado = now >= partida['question_started_at'] + float(partida['question_duration'])
            todos_respondieron = _todos_han_respondido(partida)
            
            if tiempo_agotado or todos_respondieron:
                # pasar a resultados
                partida['fase'] = 'results'
                partida['results_started_at'] = now
                partida['ultimo_resultado'] = _compute_results(partida)
                razon = "tiempo agotado" if tiempo_agotado else "todos respondieron"
                print(f"[DEBUG] PIN {pin}: Pasando a RESULTS en pregunta {partida['pregunta_actual_index']} ({razon})")

    # Avanzar de resultados a la siguiente pregunta
    if partida['estado'] == 'J' and partida['fase'] == 'results':
        if partida['results_started_at'] is not None:
            if now >= partida['results_started_at'] + RESULTS_DELAY_SECONDS:
                print(f"[DEBUG] PIN {pin}: Intentando avanzar a siguiente pregunta desde índice {partida['pregunta_actual_index']}")
                _start_next_question(pin)

    return partida


def _compute_current_ranking(partida):
    """Calcula el ranking actual ordenado por puntaje, con información de puntos ganados en esta pregunta"""
    if partida['modalidad_grupal']:
        # En modo grupal, retornar puntajes de grupos
        ranking = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        ranking_data = []
        for g in ranking:
            puntaje_anterior = partida.get('puntajes_pregunta_anterior', {}).get(g['nombre'], g['puntaje'])
            puntos_ganados = g['puntaje'] - puntaje_anterior
            ranking_data.append({
                'nombre': g['nombre'], 
                'puntaje': g['puntaje'],
                'puntos_ganados': puntos_ganados if partida['pregunta_actual_index'] >= 0 else 0
            })
        return ranking_data
    else:
        # En modo individual, retornar puntajes de participantes
        participantes_list = list(partida['participantes'].items())
        ranking = sorted(participantes_list, key=lambda x: x[1]['puntaje'], reverse=True)
        ranking_data = []
        for nombre, data in ranking:
            puntaje_anterior = partida.get('puntajes_pregunta_anterior', {}).get(nombre, data['puntaje'])
            puntos_ganados = data['puntaje'] - puntaje_anterior
            ranking_data.append({
                'nombre': nombre, 
                'puntaje': data['puntaje'],
                'puntos_ganados': puntos_ganados if partida['pregunta_actual_index'] >= 0 else 0
            })
        return ranking_data


def get_status(pin):
    partida = advance_state_if_needed(pin)
    if not partida:
        return {'existe': False}
    return {
        'existe': True,
        'estado': partida['estado'],
        'fase': partida['fase'],
    }


def get_current(pin):
    partida = advance_state_if_needed(pin)
    if not partida:
        return {'existe': False}

    nombre_usuario = session.get('nombre_usuario')
    mi_grupo = None
    if nombre_usuario and nombre_usuario in partida['participantes']:
        mi_grupo = partida['participantes'][nombre_usuario].get('grupo')

    # Generar ranking actual
    ranking_actual = _compute_current_ranking(partida)
    
    # Hora del servidor para sincronización en cliente
    servidor_ahora = time.time()

    if partida['estado'] == 'F' or partida['fase'] == 'final':
        return {'existe': True, 'estado': 'F', 'fase': 'final', 'data': _final_ranking(partida), 'mi_grupo': mi_grupo, 'ranking_actual': ranking_actual, 'servidor_ahora': servidor_ahora, 'modalidad_grupal': partida['modalidad_grupal']}

    if partida['estado'] == 'J' and partida['fase'] == 'question':
        return {'existe': True, 'estado': 'J', 'fase': 'question', 'data': _compute_question_payload(partida, nombre_usuario), 'mi_grupo': mi_grupo, 'ranking_actual': ranking_actual, 'servidor_ahora': servidor_ahora, 'modalidad_grupal': partida['modalidad_grupal']}

    if partida['estado'] == 'J' and partida['fase'] == 'results':
        return {'existe': True, 'estado': 'J', 'fase': 'results', 'data': partida.get('ultimo_resultado'), 'mi_grupo': mi_grupo, 'ranking_actual': ranking_actual, 'servidor_ahora': servidor_ahora, 'modalidad_grupal': partida['modalidad_grupal']}

    # lobby
    return {'existe': True, 'estado': partida['estado'], 'fase': partida['fase'], 'mi_grupo': mi_grupo, 'ranking_actual': ranking_actual, 'servidor_ahora': servidor_ahora, 'modalidad_grupal': partida['modalidad_grupal']}


# ---------------------------------- AGREGADO POR PAME - Reportes
#Extrae los datos de la respuesta enviada por el participante para luego invocar una funcion (log_respuesta_en_bd) que ingrese esos datos en la BD
def submit_answer(pin, id_opcion, tiempo_restante):
    partida = partidas_en_juego.get(pin) # Obtener la partida en memoria
    if not partida or partida['estado'] != 'J' or partida['fase'] != 'question':
        return False

    nombre_usuario = session.get('nombre_usuario')
    if not nombre_usuario:
        return False

    participante = partida['participantes'].get(nombre_usuario)
    if not participante:
        return False
    
    # Verificar si ya respondió esta pregunta (flag simple por pregunta)
    if participante.get('respondio_esta_pregunta', False):
        return False  # Ya respondió esta pregunta

    opcion_db = cpo.obtener_opcion_por_id(id_opcion)
    if not opcion_db:
        return False

    pregunta = partida['preguntas_data'][partida['pregunta_actual_index']]
    tiempo_total = pregunta['tiempo']

    es_correcta = opcion_db['es_correcta_bool']
    puntos = _calcular_puntos(tiempo_restante, tiempo_total) if es_correcta else 0

    if partida['modalidad_grupal']:
        nombre_grupo = participante.get('grupo')
        if not nombre_grupo:
            return False
        grupo = next((g for g in partida['grupos'] if g['nombre'] == nombre_grupo), None)
        if not grupo or grupo.get('respondio_pregunta'):
            return False
        grupo['puntaje'] += puntos
        grupo['respondio_pregunta'] = True
        # Marcar que este participante ya respondió
        participante['respondio_esta_pregunta'] = True
        participante['respuesta_correcta'] = es_correcta  # Guardar si fue correcta
        participante['id_opcion_respondida'] = id_opcion  # ⭐ Guardar opción respondida

        ctrl_partidas.log_respuesta_en_bd(
            partida, participante, pregunta, opcion_db, puntos, tiempo_restante, nombre_usuario
        )
        return True
    
    # aqui coloc mi bloque de codigo?
    # individual
    participante['puntaje'] += puntos
    participante['respondio_esta_pregunta'] = True
    participante['respuesta_correcta'] = es_correcta  # Guardar si fue correcta
    participante['id_opcion_respondida'] = id_opcion  # ⭐ Guardar opción respondida
    ctrl_partidas.log_respuesta_en_bd(
        partida, participante, pregunta, opcion_db, puntos, tiempo_restante, nombre_usuario
    )
    return True


def _final_ranking(partida):
    if partida['modalidad_grupal']:
        ranking_final = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        ranking_data = []
        for i, grupo in enumerate(ranking_final, start=1):
            # Calcular monedas para cada grupo
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
        return ranking_data
    else:
        ranking_ordenado = sorted(partida['participantes'].values(), key=lambda p: p['puntaje'], reverse=True)
        ranking_data, usados = [], set()
        posicion = 1
        for p_data in ranking_ordenado:
            for nombre, data in partida['participantes'].items():
                if data == p_data and nombre not in usados:
                    # Calcular monedas para este jugador
                    base_por_puesto = {1: 100, 2: 75, 3: 50}
                    base = base_por_puesto.get(posicion, 20)
                    extra = data['puntaje'] // 50
                    monedas = base + extra
                    
                    ranking_data.append({
                        'nombre': nombre, 
                        'puntaje': data['puntaje'],
                        'monedas': monedas,
                        'posicion': posicion
                    })
                    usados.add(nombre)
                    posicion += 1
                    break
        return ranking_data


def finalize_game(pin):
    partida = partidas_en_juego.get(pin)
    if not partida or partida['estado'] == 'F':
        return False

    partida['estado'] = 'F'
    partida['fase'] = 'final'

    # guardar puntos en DB
    if partida['modalidad_grupal']:
        ranking_final = sorted(partida['grupos'], key=lambda g: g['puntaje'], reverse=True)
        for grupo in ranking_final:
            for miembro_nombre in grupo['miembros']:
                participante_data = partida['participantes'].get(miembro_nombre)
                if participante_data and participante_data.get('id_usuario'):
                    ctrl_usuarios.sumar_puntos(participante_data['id_usuario'], grupo['puntaje'])
    else:
        ranking_final = sorted(partida['participantes'].values(), key=lambda p: p['puntaje'], reverse=True)
        usados = set()
        for p_data in ranking_final:
            for nombre, data in partida['participantes'].items():
                if data == p_data and nombre not in usados:
                    if data.get('id_usuario'):
                        ctrl_usuarios.sumar_puntos(data['id_usuario'], data['puntaje'])
                    usados.add(nombre)
                    break

    # marcar finalizado en BD
    ctrl_partidas.finalizar_partida(partida['id_partida'])
    return True
