from flask import jsonify, request, url_for, session, Response, send_file, redirect, current_app
import traceback
import os
import time
from main import app
from werkzeug.utils import secure_filename
import csv          #usado para los reportes
import io           #usado para los reportes
import pymysql
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from bd import obtener_conexion
from controladores import cuestionarios as cc
from controladores import preguntas_opciones as cpo
from controladores import controlador_partidas as c_part
from controladores import controlador_recompensas as c_rec
from controladores import usuarios as ctrl
from controladores import email_sender
from controladores.onedrive_uploader import OneDriveUploader
from ajax_game import (
    partidas_en_juego,
    _ensure_loaded,
    get_lobby_state,
    join_player,
    select_group,
    remove_player,
    start_game,
    get_status,
    get_current,
    submit_answer,
    advance_state_if_needed,
    finalize_game,
)


# --- Auxiliares --------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------


@app.route("/api/test")
def api_test():
    return jsonify({"mensaje": "La API funciona correctamente"})


# ------------------------------------------------------------------------------
# USUARIOS


@app.route("/api/usuarios", methods=['GET'])
def api_get_usuarios():
    # Lógica para llamar al controlador que obtiene todos los usuarios
    # usuarios = controladores.usuarios.obtener_todos()
    return jsonify({"mensaje": "Devuelve lista de usuarios"})


@app.route("/api/usuarios", methods=['POST'])
def api_create_usuario():
    data = request.get_json(force=True) or {}
    nombre_completo = (data.get("nombre_completo") or "").strip()
    nombre_usuario  = (data.get("nombre_usuario")  or "").strip()
    correo          = (data.get("correo")          or "").strip().lower()
    contrasena      = (data.get("contrasena")      or "")
    tipo            = (data.get("tipo")            or "E").strip()

    if not (nombre_completo and nombre_usuario and correo and contrasena):
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    modo = (request.args.get("modo") or "pendiente").lower()
    if modo == "directo":
        ok, msg = ctrl.crear_usuario(nombre_completo, nombre_usuario, correo, contrasena, tipo)
        return (jsonify({"ok": True, "mensaje": msg}), 201) if ok else (jsonify({"error": msg}), 409)

    ok, resultado = ctrl.crear_usuario_pendiente(nombre_completo, nombre_usuario, correo, contrasena, tipo)
    if ok:
        return jsonify({"ok": True, "codigo_verificacion": resultado}), 201
    return jsonify({"error": resultado}), 409

@app.route("/api/usuarios/verificacion", methods=["POST"])
def usuarios_verificar():
    data = request.get_json(force=True) or {}
    correo = (data.get("correo") or "").strip().lower()
    codigo = (data.get("codigo") or "").strip()
    if not (correo and codigo):
        return jsonify({"error": "correo y codigo son obligatorios"}), 400

    res = ctrl.verificar_y_activar_usuario(correo, codigo)
    if res == "OK":
        return jsonify({"ok": True}), 200
    return jsonify({"error": res}), 400

@app.route("/api/usuarios/<int:id_usuario>", methods=['GET'])
def api_get_usuario(id_usuario):
    u = ctrl.obtener_por_id(id_usuario)
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404
    # no exponer contraseña
    u.pop("contraseña", None)
    return jsonify(u), 200


@app.route("/api/usuarios/<int:id_usuario>", methods=['PUT'])
def api_update_usuario(id_usuario):
    # Lógica para actualizar un usuario
    actual = ctrl.obtener_por_id(id_usuario)
    if not actual:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json(force=True) or {}

    # merge con valores actuales
    nombre_completo = (data.get("nombre_completo") or actual["nombre_completo"]).strip()
    nombre_usuario  = (data.get("nombre_usuario")  or actual["nombre_usuario"]).strip()
    correo          = (data.get("correo")          or actual["correo"]).strip().lower()
    tipo            = (data.get("tipo")            or actual["tipo"]).strip()
    puntos          = int(data.get("puntos")  if data.get("puntos")  is not None else actual["puntos"])
    monedas         = int(data.get("monedas") if data.get("monedas") is not None else actual["monedas"])
    vigente         = bool(data.get("vigente") if data.get("vigente") is not None else actual["vigente"])

    # unicidad correo / nombre_usuario (excluyendo mi propio id)
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as c:
            c.execute("SELECT id_usuario FROM USUARIO WHERE correo=%s AND id_usuario<>%s LIMIT 1", (correo, id_usuario))
            if c.fetchone():
                return jsonify({"error":"El correo ya está en uso", "campo":"correo"}), 409
            c.execute("SELECT id_usuario FROM USUARIO WHERE nombre_usuario=%s AND id_usuario<>%s LIMIT 1", (nombre_usuario, id_usuario))
            if c.fetchone():
                return jsonify({"error":"El nombre de usuario ya está en uso", "campo":"nombre_usuario"}), 409
    finally:
        if conexion:
            conexion.close()

    ctrl.actualizar(id_usuario, nombre_completo, nombre_usuario, correo, tipo, puntos, monedas, vigente)
    actualizado = ctrl.obtener_por_id(id_usuario)
    actualizado.pop("contraseña", None)
    return jsonify(actualizado), 200

@app.route("/api/usuarios/<int:id_usuario>/cambiar_password", methods=['POST'])
def api_cambiar_password(id_usuario):
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Solicitud inválida"}), 400

    antigua = (data.get("actual") or "").strip()
    nueva   = (data.get("nueva")  or "").strip()

    if not antigua or not nueva:
        return jsonify({"error": "Faltan datos"}), 400

    ok, msg = ctrl.actualizar_contrasena(id_usuario, antigua, nueva)

    if ok:
        return jsonify({"ok": True}), 200

    # Mapeo de mensajes a lo que espera el frontend
    m = (msg or "").lower()
    if "usuario no encontrado" in m:
        return jsonify({"error": "Usuario no encontrado"}), 404
    if "contraseña actual es incorrecta" in m or "contrasena actual es incorrecta" in m:
        return jsonify({"error": "Tu contraseña actual no es la correcta"}), 409

    return jsonify({"error": "Algo salió mal, vuelve a intentarlo"}), 500

@app.route("/api/usuarios/<int:id_usuario>", methods=['DELETE'])
def api_delete_usuario(id_usuario):
    # Lógica para eliminar (o desactivar) un usuario
    if not ctrl.obtener_por_id(id_usuario):
        return jsonify({"error": "Usuario no encontrado"}), 404

    ok = ctrl.desactivar(id_usuario)  # True/False
    if not ok:
        # No se afectó ninguna fila
        return jsonify({"error": "No se pudo desactivar el usuario"}), 500

    return jsonify({"ok": True, "id_usuario": id_usuario, "vigente": False}), 200

@app.route("/api/verificar_correo/<correo>")
def verificar_correo(correo):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT vigente FROM USUARIO WHERE correo = %s"
        cursor.execute(query, (correo,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            return jsonify({"existe": True, "vigente": bool(usuario["vigente"])})
        else:
            return jsonify({"existe": False, "vigente": False})
    except Exception as e:
        print("Error en verificar_correo:", e)
        return jsonify({"error": "Error interno"}), 500


@app.get("/api/correo_activo")
def api_correo_activo():
    correo = (request.args.get("correo") or "").strip()
    if not correo:
        return jsonify({"ok": False, "error": "correo_requerido"}), 400

    require_verificado = request.args.get("require_verificado", "false").lower() == "true"

    try:
        valido = ctrl.correo_activo(correo, require_verificado=require_verificado)
        return jsonify({"ok": True, "valido": bool(valido), "require_verificado": require_verificado}), 200
    except Exception:
        traceback.print_exc()  # <-- log más útil
        return jsonify({"ok": False, "error": "interno"}), 500
# ------------------------------------------------------------------------------
# CUESTIONARIOS Y SUS PARTES


@app.route("/api/cuestionarios", methods=['GET'])
def api_get_cuestionarios():
    try:
        # Leemos los filtros opcionales de la URL
        id_usuario = request.args.get('id_usuario', type=int)
        id_categoria = request.args.get('id_categoria', type=int)
        es_publico = request.args.get('publico', type=bool)

        # Llamamos al controlador con los filtros
        cuestionarios = cc.obtener_con_filtros(id_usuario, id_categoria, es_publico)
        return jsonify({"data": cuestionarios}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cuestionarios", methods=['POST'])
def api_create_cuestionario():
    try:
        data = request.json
        cc.crear(
            titulo=data['titulo'],
            descripcion=data['descripcion'],
            es_publico=data['es_publico'],
            id_usuario=data['id_usuario'],
            id_categoria=data['id_categoria'],
            id_cuestionario_original=data.get('id_cuestionario_original') # .get() para campos opcionales
        )
        return jsonify({"mensaje": "Cuestionario creado con éxito"}), 201
    except KeyError:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cuestionarios/<int:id_cuestionario>", methods=['GET'])
def api_get_cuestionario(id_cuestionario):
    cuestionario = cc.obtener_por_id(id_cuestionario)
    if cuestionario:
        return jsonify({"data": cuestionario}), 200
    return jsonify({"mensaje": "Cuestionario no encontrado"}), 404


@app.route("/api/cuestionarios", methods=['PUT'])
def api_update_cuestionario():
    try:
        data = request.json
        cc.actualizar(
            id_cuestionario=data['id_cuestionario'],
            titulo=data['titulo'],
            descripcion=data['descripcion'],
            es_publico=data['es_publico'],
            #id_usuario=data['id_usuario'],
            id_categoria=data['id_categoria'],
            vigente=data['vigente']
        )
        return jsonify({"mensaje": "Cuestionario actualizado con éxito"}), 201
    except KeyError:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cuestionarios/<int:id_cuestionario>", methods=['DELETE'])
def api_delete_cuestionario(id_cuestionario):
    try:
        # Llama a la función del controlador para desactivar
        exito = cc.desactivar(id_cuestionario)

        if exito:
            return jsonify({"mensaje": "Cuestionario desactivado correctamente"}), 200
        else:
            return jsonify({"error": "Cuestionario no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cuestionarios/guardar-completo", methods=['POST'])
def api_guardar_cuestionario_completo():
    data = request.json # Aquí recibes el objeto cuestionarioData completo

    # Llama a una nueva función del controlador que se encargue de todo
    # Esta función debe usar una "transacción" para asegurar que todo se guarde correctamente
    id_cuestionario_guardado = cc.guardar_o_actualizar_completo(data)

    return jsonify({"mensaje": "Cuestionario guardado con éxito", "id_cuestionario": id_cuestionario_guardado})


@app.route("/api/preguntas/<int:id_pregunta>/imagen", methods=['POST'])
def api_upload_pregunta_imagen(id_pregunta):
    if 'imagen' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400

    file = request.files['imagen']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    if file and allowed_file(file.filename):
        # 1. Obtenemos el id_cuestionario para crear la carpeta correcta
        pregunta = cpo.obtener_pregunta_por_id(id_pregunta)
        if not pregunta:
            return jsonify({"error": "La pregunta no existe"}), 404
        id_cuestionario = pregunta['id_cuestionario']

        # 2. Creamos un nombre de archivo seguro y único
        ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time())
        filename = secure_filename(f"pregunta_{id_pregunta}_{timestamp}.{ext}")

        # 3. Creamos la ruta y la carpeta si no existe
        upload_folder = os.path.join(app.root_path, 'static', 'img', 'cuestionarios', f'c_{id_cuestionario}')
        os.makedirs(upload_folder, exist_ok=True)

        # 4. Guardamos el archivo en el servidor
        file.save(os.path.join(upload_folder, filename))

        # 5. Guardamos la ruta relativa en la base de datos
        ruta_para_bd = f"img/cuestionarios/c_{id_cuestionario}/{filename}"
        cpo.actualizar_ruta_imagen(id_pregunta, ruta_para_bd)

        return jsonify({"mensaje": "Imagen subida con éxito", "ruta_img": ruta_para_bd}), 200

    return jsonify({"error": "Tipo de archivo no permitido"}), 400


@app.route("/api/preguntas/<int:id_pregunta>/imagen", methods=['DELETE'])
def api_delete_pregunta_imagen(id_pregunta):
    exito = cpo.quitar_imagen_pregunta(id_pregunta)
    if exito:
        return jsonify({"mensaje": "Imagen eliminada con éxito"}), 200
    else:
        return jsonify({"error": "No se pudo eliminar la imagen"}), 500




# --- PREGUNTAS ---

@app.route("/api/cuestionarios/<int:id_cuestionario>/preguntas", methods=['GET'])
def api_get_preguntas(id_cuestionario):
    preguntas = cpo.obtener_preguntas_por_cuestionario(id_cuestionario)
    return jsonify({"data": preguntas}), 200


@app.route("/api/cuestionarios/<int:id_cuestionario>/preguntas", methods=['POST'])
def api_create_pregunta(id_cuestionario):
    try:
        data = request.json
        cpo.crear_pregunta(
            id_cuestionario=id_cuestionario,
            pregunta=data['pregunta'],
            num_pregunta=data['num_pregunta'],
            puntaje_base=data['puntaje_base'],
            adjunto=data.get('adjunto')
        )
        return jsonify({"mensaje": "Pregunta creada con éxito"}), 201
    except KeyError:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/preguntas/<int:id_pregunta>", methods=['GET'])
def api_get_pregunta_por_id(id_pregunta):
    pregunta = cpo.obtener_pregunta_por_id(id_pregunta)
    return jsonify({"data": pregunta}) if pregunta else (jsonify({"error": "Pregunta no encontrada"}), 404)


@app.route("/api/preguntas/<int:id_pregunta>", methods=['PUT'])
def api_update_pregunta(id_pregunta):
    data = request.json
    cpo.actualizar_pregunta(id_pregunta, data['pregunta'], data['puntaje_base'])
    return jsonify({"mensaje": "Pregunta actualizada"})


@app.route("/api/preguntas/<int:id_pregunta>", methods=['DELETE'])
def api_delete_pregunta(id_pregunta):
    cpo.eliminar_pregunta(id_pregunta)
    return jsonify({"mensaje": "Pregunta eliminada"})


# --- OPCIONES ---

@app.route("/api/preguntas/<int:id_pregunta>/opciones", methods=['GET'])
def api_get_opciones(id_pregunta):
    opciones = cpo.obtener_opciones_por_pregunta(id_pregunta)
    return jsonify({"data": opciones}), 200


@app.route("/api/preguntas/<int:id_pregunta>/opciones", methods=['POST'])
def api_create_opcion(id_pregunta):
    try:
        data = request.json
        cpo.crear_opcion(
            id_pregunta=id_pregunta,
            opcion=data['opcion'],
            es_correcta_bool=data['es_correcta_bool'],
            descripcion=data.get('descripcion'),
            adjunto=data.get('adjunto')
        )
        return jsonify({"mensaje": "Opción creada con éxito"}), 201
    except KeyError:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/opciones/<int:id_opcion>", methods=['GET'])
def api_get_opcion_por_id(id_opcion):
    opcion = cpo.obtener_opcion_por_id(id_opcion)
    return jsonify({"data": opcion}) if opcion else (jsonify({"error": "Opción no encontrada"}), 404)

@app.route("/api/opciones/<int:id_opcion>", methods=['PUT'])
def api_update_opcion(id_opcion):
    data = request.json
    cpo.actualizar_opcion(id_opcion, data['opcion'])
    return jsonify({"mensaje": "Opción actualizada"})


@app.route("/api/opciones/<int:id_opcion>", methods=['DELETE'])
def api_delete_opcion(id_opcion):
    cpo.eliminar_opcion(id_opcion)
    return jsonify({"mensaje": "Opción eliminada"})


# ------------------------------------------------------------------------------
# PARTIDAS (SESIONES DE JUEGO)


@app.route("/api/partidas", methods=['POST'])
def api_create_partida():
    # Lógica para crear una partida a partir de un id_cuestionario
    # Debería generar un PIN y devolverlo
    return jsonify({"mensaje": "Inicia una nueva partida y devuelve el PIN"}), 201


@app.route("/api/partidas/pin/<string:pin>", methods=['GET'])
def api_get_partida_by_pin(pin):
    # Lógica para que un jugador obtenga datos de la partida antes de unirse
    return jsonify({"mensaje": f"Devuelve info de la partida con PIN {pin}"})


@app.route("/api/partidas/<int:id_partida>/participantes", methods=['POST'])
def api_join_partida(id_partida):
    # Lógica para que un participante se una a una partida
    return jsonify({"mensaje": f"Un jugador se une a la partida {id_partida}"}), 201


@app.route("/api/partidas/<int:id_partida>/respuestas", methods=['POST'])
def api_submit_respuesta(id_partida):
    # Lógica para que un participante envíe su respuesta
    # Recibe: id_participante, id_opcion, tiempo_respuesta
    return jsonify({"mensaje": "Un jugador envía una respuesta"})

    #-------------------RECOMPENSAS----------------------------------


@app.route("/api/partidas/<int:id_partida>/finalizar", methods=['POST'])
def api_finalizar_partida(id_partida):
    """Finaliza una partida, otorga recompensas y muestra cambios en monedas."""
    import traceback
    import pymysql

    try:
        conexion = obtener_conexion()
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            # Verificar si la partida existe
            cursor.execute("SELECT estado FROM PARTIDA WHERE id_partida = %s", (id_partida,))
            partida = cursor.fetchone()
            if not partida:
                return jsonify({"error": f"La partida {id_partida} no existe"}), 404
            if partida["estado"] == "F":
                return jsonify({"mensaje": f"La partida {id_partida} ya estaba finalizada"}), 200

            # Obtener datos antes de otorgar recompensas
            cursor.execute("""
                SELECT p.id_usuario, u.nombre_completo, p.puntaje, u.monedas
                FROM PARTICIPANTE p
                JOIN USUARIO u ON p.id_usuario = u.id_usuario
                WHERE p.id_partida = %s
            """, (id_partida,))
            antes = cursor.fetchall()

        # Finalizar partida
        exito = c_part.finalizar_partida(id_partida)
        if not exito:
            return jsonify({"error": "No se pudo finalizar la partida"}), 500

        # Obtener datos después de otorgar recompensas
        conexion = obtener_conexion()
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT p.id_usuario, u.nombre_completo, p.puntaje, u.monedas
                FROM PARTICIPANTE p
                JOIN USUARIO u ON p.id_usuario = u.id_usuario
                WHERE p.id_partida = %s
            """, (id_partida,))
            despues = cursor.fetchall()

        conexion.close()

        # Comparar resultados
        resumen = []
        for a in antes:
            d = next((x for x in despues if x["id_usuario"] == a["id_usuario"]), None)
            if d:
                resumen.append({
                    "id_usuario": a["id_usuario"],
                    "participante": a["nombre_completo"],
                    "puntaje": a["puntaje"],
                    "monedas_antes": a["monedas"],
                    "monedas_despues": d["monedas"],
                    "diferencia": d["monedas"] - a["monedas"]
                })

        return jsonify({
            "mensaje": f"Partida {id_partida} finalizada y recompensas otorgadas correctamente",
            "recompensas": resumen
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Error interno al finalizar la partida",
            "detalle": str(e),
            "traza": traceback.format_exc()
        }), 500


# ---------------------------
# AJAX GAME (sin sockets)

@app.post('/api/game/host/init')
def api_game_host_init():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    partida = _ensure_loaded(pin)
    if not partida:
        return jsonify({'error': 'PIN inválido o no disponible'}), 404
    return jsonify({'ok': True, 'lobby': get_lobby_state(pin), 'estado': partida['estado'], 'fase': partida['fase']})


@app.get('/api/lobby/state')
def api_lobby_state():
    pin = (request.args.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    if not _ensure_loaded(pin):
        return jsonify({'error': 'PIN inválido'}), 404
    return jsonify(get_lobby_state(pin))


@app.post('/api/player/join')
def api_player_join():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    if not _ensure_loaded(pin):
        return jsonify({'error': 'PIN inválido'}), 404
    partida = join_player(pin)
    if not partida:
        return jsonify({'error': 'no se pudo unir'}), 400
    st = get_status(pin)
    return jsonify({'ok': True, 'estado': st.get('estado'), 'fase': st.get('fase'), 'lobby': get_lobby_state(pin)})


@app.post('/api/player/select-group')
def api_player_select_group():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    nombre_grupo = (data.get('nombre_grupo') or '').strip()
    if not pin or not nombre_grupo:
        return jsonify({'error': 'pin y nombre_grupo requeridos'}), 400
    if not _ensure_loaded(pin):
        return jsonify({'error': 'PIN inválido'}), 404
    ok = select_group(pin, nombre_grupo)
    if not ok:
        return jsonify({'error': 'no se pudo seleccionar grupo'}), 400
    return jsonify({'ok': True, 'lobby': get_lobby_state(pin)})


@app.post('/api/player/leave')
def api_player_leave():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    if not _ensure_loaded(pin):
        return jsonify({'error': 'PIN inválido'}), 404
    ok = remove_player(pin)
    if not ok:
        return jsonify({'error': 'no se pudo salir'}), 400
    return jsonify({'ok': True})


@app.post('/api/game/start')
def api_game_start():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    if not _ensure_loaded(pin):
        return jsonify({'error': 'PIN inválido'}), 404
    started = start_game(pin)
    return jsonify({'started': bool(started)})


@app.get('/api/game/status')
def api_game_status():
    pin = (request.args.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    st = get_status(pin)
    if not st.get('existe'):
        return jsonify({'error': 'PIN inválido'}), 404
    resp = {'estado': st['estado'], 'fase': st['fase']}
    if st['estado'] == 'J':
        resp['url'] = url_for('pagina_juego', pin=pin)
    return jsonify(resp)


@app.get('/api/game/current')
def api_game_current():
    pin = (request.args.get('pin') or '').strip().upper()
    if not pin:
        return jsonify({'error': 'pin requerido'}), 400
    cur = get_current(pin)
    if not cur.get('existe'):
        return jsonify({'error': 'PIN inválido'}), 404
    return jsonify(cur)


@app.post('/api/game/answer')
def api_game_answer():
    data = request.get_json(force=True) or {}
    pin = (data.get('pin') or '').strip().upper()
    id_opcion = data.get('id_opcion')
    tiempo_restante = data.get('tiempo_restante', 0)
    if not pin or id_opcion is None:
        return jsonify({'error': 'pin e id_opcion requeridos'}), 400
    
    # Obtener info de la pregunta actual
    partida = partidas_en_juego.get(pin)
    respuesta_correcta = None
    es_correcta = False
    mi_puntaje = 0
    
    if not partida or partida['fase'] != 'question':
        return jsonify({'error': 'No hay pregunta activa'}), 400
    
    pregunta = partida['preguntas_data'][partida['pregunta_actual_index']]
    opciones = cpo.obtener_opciones_por_pregunta(pregunta['id_pregunta'])
    
    # Verificar si la opción seleccionada es correcta
    opcion_seleccionada = next((o for o in opciones if o['id_opcion'] == id_opcion), None)
    if opcion_seleccionada:
        es_correcta = opcion_seleccionada.get('es_correcta_bool', False)
    
    # Encontrar texto de la opción correcta
    for o in opciones:
        if o.get('es_correcta_bool'):
            respuesta_correcta = o['opcion']
            break
    
    # ENVIAR LA RESPUESTA (esto calcula y suma los puntos)
    ok = submit_answer(pin, id_opcion, tiempo_restante)
    
    # AHORA obtener el puntaje ACTUALIZADO
    if ok:
        nombre_usuario = session.get('nombre_usuario')
        if nombre_usuario and nombre_usuario in partida['participantes']:
            participante = partida['participantes'][nombre_usuario]
            if partida['modalidad_grupal']:
                nombre_grupo = participante.get('grupo')
                if nombre_grupo:
                    grupo = next((g for g in partida['grupos'] if g['nombre'] == nombre_grupo), None)
                    if grupo:
                        mi_puntaje = grupo['puntaje']
            else:
                mi_puntaje = participante['puntaje']
    
    return jsonify({
        'ok': bool(ok),
        'respuesta_correcta': respuesta_correcta,
        'es_correcta': es_correcta,
        'mi_puntaje': mi_puntaje,
        'nombre_quien_respondio': session.get('nombre_usuario', 'Compañero'),  # ⭐ Para modal grupal
        'texto_opcion': opcion_seleccionada.get('opcion', 'Opción desconocida') if opcion_seleccionada else 'Opción desconocida'  # ⭐ Para modal grupal
    })

#------------------CODIGO PARA ACCEDER AL CUESTIONARIO EN MODO VISUALIZACION------


@app.route("/api/validar-codigo-sesion", methods=['POST'])
def api_validar_codigo_sesion():
    """Valida el código (PIN) de una sesión y devuelve el id_cuestionario asociado"""
    try:
        data = request.get_json(force=True) or {}
        codigo = (data.get("codigo") or "").strip().upper()

        if not codigo or len(codigo) != 6:
            return jsonify({"error": "El código debe tener 6 caracteres"}), 400

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # Buscar partida con ese PIN que esté activa (estado 'E' o 'P')
                cursor.execute("""
                    SELECT p.id_partida, p.id_cuestionario, p.estado, c.titulo
                    FROM PARTIDA p
                    JOIN CUESTIONARIO c ON p.id_cuestionario = c.id_cuestionario
                    WHERE p.pin = %s AND p.estado IN ('E', 'P')
                    LIMIT 1
                """, (codigo,))

                partida = cursor.fetchone()

                if not partida:
                    return jsonify({"error": "Código de sesión inválido o expirado"}), 404

                return jsonify({
                    "ok": True,
                    "id_cuestionario": partida["id_cuestionario"],
                    "titulo": partida["titulo"],
                    "id_partida": partida["id_partida"]
                }), 200


        finally:
            conexion.close()

    except Exception as e:

        return jsonify({
            "error": "Error al validar el código",
            "detalle": str(e),
            "trace": traceback.format_exc()
        }), 500


#@app.route("/api/validar-codigo-sesion", methods=['POST'])
#def api_validar_codigo_sesion():
#    """Valida el código (PIN) de una sesión y devuelve el id_cuestionario asociado"""
#    try:
#        data = request.get_json(force=True) or {}
#        codigo = (data.get("codigo") or "").strip().upper()
#
#        if not codigo or len(codigo) != 6:
#            return jsonify({"error": "El código debe tener 6 caracteres"}), 400
#
#        conexion = obtener_conexion()
#        try:
#            with conexion.cursor() as cursor:
#                # Buscar partida con ese PIN (cualquier estado: E, P o F)
#                cursor.execute("""
#                    SELECT
#                        p.id_partida,
#                        p.id_cuestionario,
#                        p.estado,
#                        c.titulo,
#                        CASE
#                            WHEN p.estado = 'E' THEN 'En espera'
#                            WHEN p.estado = 'P' THEN 'En progreso'
#                           WHEN p.estado = 'F' THEN 'Finalizada'
#                        END as estado_texto
#                    FROM PARTIDA p
#                    JOIN CUESTIONARIO c ON p.id_cuestionario = c.id_cuestionario
#                    WHERE p.pin = %s
#                    LIMIT 1
#                """, (codigo,))
#
#                partida = cursor.fetchone()
#
#                if not partida:
#                    return jsonify({"error": "Código de sesión inválido"}), 404

#                # Validar según el estado
#                id_partida, id_cuestionario, estado, titulo, estado_texto = partida
#
#                # OPCIÓN A: Permitir todos los estados
#                return jsonify({
#                    "ok": True,
#                    "id_cuestionario": id_cuestionario,
#                    "titulo": titulo,
#                    "id_partida": id_partida,
#                    "estado": estado,
#                    "estado_texto": estado_texto
#                }), 200

                # OPCIÓN B: Solo permitir E y P (descomenta para usar)
                # if estado not in ('E', 'P'):
                #     return jsonify({
                #         "error": f"Esta sesión ya ha finalizado. Estado actual: {estado_texto}"
                #     }), 403

                # OPCIÓN C: Solo permitir E (descomenta para usar)
                # if estado != 'E':
                #     return jsonify({
                #         "error": f"Esta sesión ya comenzó o finalizó. Estado: {estado_texto}"
                #     }), 403

#        finally:
#            conexion.close()

    except Exception as e:
        return jsonify({"error": "Error al validar el código", "detalle": str(e)}), 500

# --- INICIO: NUEVO ENDPOINT PARA SOLICITAR RESTABLECIMIENTO ---

@app.route("/api/solicitar-restablecimiento", methods=['POST'])
def api_solicitar_restablecimiento():
    data = request.get_json()
    if not data or 'correo' not in data:
        return jsonify({"error": "Falta el campo 'correo'."}), 400

    correo = (data['correo'] or '').strip().lower()

    # Consulta "fuerte": solo trae si está vigente y verificado
    usuario_ok = ctrl.obtener_por_correo(correo)

    if not usuario_ok:
        # Consulta adicional para diferenciar si es "no verificado" o "no existe"
        usuario_any = ctrl.obtener_por_correo_sin_filtros(correo)
        if usuario_any and usuario_any.get('vigente') and not usuario_any.get('verificado'):
            return jsonify({"mensaje": "No has verificado el correo que has ingresado."}), 200

        # Genérico para no enumerar
        return jsonify({"mensaje": "Si tu correo está en nuestro sistema, recibirás un enlace para restablecer tu contraseña."}), 200

    # Si llegó acá, está vigente y verificado → envía correo
    try:
        token = ctrl.generar_token_restablecimiento(usuario_ok['id_usuario'])
        url_de_restablecimiento = url_for('restablecer_con_token', token=token, _external=True)
        enviado, mensaje_email = email_sender.enviar_correo_restablecimiento(usuario_ok['correo'], url_de_restablecimiento)
        if not enviado:
            return jsonify({"error": f"No se pudo enviar el correo. Detalles: {mensaje_email}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    return jsonify({"mensaje": "Si tu correo está en nuestro sistema, recibirás un enlace para restablecer tu contraseña."}), 200
# --- FIN: NUEVO ENDPOINT ---

# ---------------------------------- AGREGADO POR PAME - Reportes
# --- GAME: submit answer ---
@app.route("/api/game/submit", methods=["POST"])
def api_game_submit():
    try:
        data = request.get_json() or {}
        pin = data.get("pin")
        id_opcion = data.get("id_opcion")
        tiempo_restante = data.get("tiempo_restante")  # segundos restantes (int)

        if not pin or not id_opcion:
            return jsonify({"ok": False, "msg": "Faltan pin o id_opcion"}), 400

        from ajax_game import submit_answer
        ok = submit_answer(pin, id_opcion, tiempo_restante)
        return jsonify({"ok": bool(ok)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500

# ---------- REPORTES JSON ----------
@app.route("/api/report/partida", methods=["GET"])
def api_report_partida():
    """
    Uso:
        /api/report/partida?pin=AB12CD
    ó  /api/report/partida?id_partida=123
    Devuelve JSON con header, resumen, preguntas, participantes.
    """
    try:
        pin = request.args.get("pin")
        id_partida = request.args.get("id_partida", type=int)

        if not pin and not id_partida:
            return jsonify({"ok": False, "msg": "Proporcione pin o id_partida"}), 400

        from controladores import controlador_partidas as c_part

        if pin:
            data = c_part.reporte_por_pin(pin)
        else:
            data = c_part.reporte_por_partida_id(id_partida)

        if not data:
            return jsonify({"ok": False, "msg": "Partida no encontrada"}), 404

        return jsonify({"ok": True, "data": data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500


# ---------- REPORTES CSV (descarga) ----------
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from flask import send_file
import io

@app.route("/api/report/partida/export", methods=["GET"])
def api_report_partida_export():
    """
    Exporta Excel con múltiples hojas: Resumen, Detalle por participante, Detalle por pregunta
    Uso: /api/report/partida/export?pin=AB12CD o /api/report/partida/export?id_partida=123
    """
    try:
        pin = request.args.get("pin")
        id_partida = request.args.get("id_partida", type=int)

        from controladores import controlador_partidas as c_part
        
        # Obtener datos completos del reporte
        if pin:
            data = c_part.reporte_por_pin(pin)
        elif id_partida:
            data = c_part.reporte_por_partida_id(id_partida)
        else:
            return jsonify({"ok": False, "msg": "Proporcione pin o id_partida"}), 400

        target_partida_id = id_partida if id_partida else data['header']['id_partida']

        # existing_report = None
        # cx_lookup = obtener_conexion()
        # try:
        #     with cx_lookup.cursor() as c_lookup:
        #         c_lookup.execute(
        #             """
        #             SELECT id_reporte, ruta
        #                 FROM REPORTE
        #                 WHERE id_partida=%s AND tipo='excel' AND subido_a='local'
        #                 ORDER BY creado_en DESC
        #                 LIMIT 1
        #         """,
        #             (target_partida_id,)
        #         )
        #         existing_report = c_lookup.fetchone()
        # finally:
        #     cx_lookup.close()

        # Crear libro Excel
        wb = Workbook()
        wb.remove(wb.active)  # Eliminar hoja por defecto

        def _set_dimensions(sheet):
            max_col = sheet.max_column or 1
            max_row = sheet.max_row or 1
            for col_idx in range(1, max_col + 1):
                sheet.column_dimensions[get_column_letter(col_idx)].width = 20
            for row_idx in range(1, max_row + 1):
                sheet.row_dimensions[row_idx].height = 20

        # --- HOJA 1: RESUMEN (Ranking Final) ---
        ws_resumen = wb.create_sheet("Resumen")
        ws_resumen.append(["Posición", "Usuario/Grupo", "PuntajeTotal", "RespuestasCorrectas", 
                          "RespuestasIncorrectas", "%Acierto", "TiempoPromedioResp (s)"])
        
        # Estilo para encabezados
        for cell in ws_resumen[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Llenar datos del ranking
        for idx, part in enumerate(data['participantes'], start=1):
            total_resp = int(part['correctas']) + int(part['incorrectas'])
            pct_acierto = round((int(part['correctas']) / total_resp * 100), 2) if total_resp > 0 else 0
            ws_resumen.append([
                idx,
                part['nombre'],
                int(part['puntaje_total']),
                int(part['correctas']),
                int(part['incorrectas']),
                pct_acierto,
                round(float(part['tiempo_prom_seg'] or 0), 2)
            ])
        _set_dimensions(ws_resumen)

        # --- HOJA 2: DETALLE POR PARTICIPANTE ---
        ws_detalle_part = wb.create_sheet("Detalle por participante")
        ws_detalle_part.append(["Usuario", "Grupo(opc)", "Correcta", 
                                "TiempoRestante", "PuntosOtorgados", "PuntajeAcumulado"])
        
        for cell in ws_detalle_part[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        # Obtener respuestas detalladas por participante
        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT pa.nombre, pa.id_grupo, rp.id_pregunta, rp.es_correcta,
                           TIME_TO_SEC(rp.tiempo_respuesta) AS tiempo_seg, rp.puntaje,
                           (SELECT SUM(rp2.puntaje) 
                            FROM RESPUESTA_PARTICIPANTE rp2 
                            WHERE rp2.id_participante = rp.id_participante 
                            AND rp2.id_respuesta <= rp.id_respuesta) AS puntaje_acum
                    FROM RESPUESTA_PARTICIPANTE rp
                    JOIN PARTICIPANTE pa ON pa.id_participante = rp.id_participante
                    WHERE rp.id_partida=%s
                    ORDER BY pa.nombre, rp.id_pregunta
                """, (target_partida_id,))
                rows_part = c.fetchall()
                
                for r in rows_part:
                    grupo = r['id_grupo']
                    ws_detalle_part.append([
                        r['nombre'],
                        grupo if grupo not in (None, "") else "No",
                        "Sí" if int(r['es_correcta']) == 1 else "No",
                        int(r['tiempo_seg'] or 0),
                        int(r['puntaje']),
                        int(r['puntaje_acum'] or 0)
                    ])
        finally:
            cx.close()
        _set_dimensions(ws_detalle_part)

        # --- HOJA 3: DETALLE POR PREGUNTA ---
        ws_detalle_preg = wb.create_sheet("Detalle por pregunta")
        ws_detalle_preg.append(["#Pregunta", "Pregunta", "Opción", "Correcta", 
                               "RespuestasRecibidas", "Aciertos", "%Aciertos"])
        
        for cell in ws_detalle_preg[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        # Obtener detalle de opciones por pregunta
        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT rp.id_pregunta, 
                           MIN(rp.pregunta_texto) AS pregunta_texto,
                           rp.opcion_texto,
                           MAX(rp.es_correcta) AS es_correcta,
                           COUNT(*) AS respuestas_recibidas,
                           SUM(rp.es_correcta) AS aciertos,
                           ROUND(AVG(TIME_TO_SEC(rp.tiempo_respuesta)), 2) AS tiempo_prom
                    FROM RESPUESTA_PARTICIPANTE rp
                    WHERE rp.id_partida=%s
                    GROUP BY rp.id_pregunta, rp.opcion_texto
                    ORDER BY rp.id_pregunta, rp.opcion_texto
                """, (target_partida_id,))
                rows_preg = c.fetchall()
                
                for r in rows_preg:
                    pct_aciertos = round((int(r['aciertos']) / int(r['respuestas_recibidas']) * 100), 2) if r['respuestas_recibidas'] > 0 else 0
                    ws_detalle_preg.append([
                        r['id_pregunta'],
                        r['pregunta_texto'],
                        r['opcion_texto'],
                        "Sí" if int(r['es_correcta']) == 1 else "No",
                        int(r['respuestas_recibidas']),
                        int(r['aciertos']),
                        pct_aciertos,
                    ])
        finally:
            cx.close()
        _set_dimensions(ws_detalle_preg)

        # timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        # filename = f"reporte_partida_{target_partida_id}_{timestamp}.xlsx"
        #
        # reports_dir = os.path.join(current_app.root_path, 'static', 'reportes', 'partidas')
        # os.makedirs(reports_dir, exist_ok=True)
        # abs_path = os.path.join(reports_dir, filename)
        #
        # wb.save(abs_path)
        #
        # rel_path = os.path.relpath(abs_path, os.path.join(current_app.root_path, 'static'))
        # rel_path = rel_path.replace("\\", "/")
        #
        # if existing_report and existing_report.get('ruta'):
        #     old_path = os.path.join(current_app.root_path, 'static', existing_report['ruta'].lstrip('/'))
        #     if os.path.isfile(old_path):
        #         try:
        #             os.remove(old_path)
        #         except OSError:
        #             pass
        #
        # cx_db = obtener_conexion()
        # try:
        #     with cx_db.cursor() as cdb:
        #         if existing_report:
        #             cdb.execute(
        #                 """
        #                 UPDATE REPORTE
        #                     SET ruta=%s,
        #                         tipo='excel',
        #                         subido_a='local',
        #                         link_externo=NULL,
        #                         creado_en=NOW()
        #                 WHERE id_reporte=%s
        #             """,
        #                 (rel_path, existing_report['id_reporte'])
        #             )
        #         else:
        #             cdb.execute(
        #                 """
        #                 INSERT INTO REPORTE (id_partida, ruta, tipo, subido_a)
        #                 VALUES (%s, %s, %s, %s)
        #             """,
        #                 (target_partida_id, rel_path, 'excel', 'local')
        #             )
        #     cx_db.commit()
        # finally:
        #     cx_db.close()

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"reporte_partida_{target_partida_id}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/api/report/partida/export-drive", methods=["GET"])
def api_report_partida_export_drive():
    """
    Genera Excel y lo sube a Google Drive en la carpeta 'DogeHoot Reportes' y lo comparte con un correo
    Uso: /api/report/partida/export-drive?pin=AB12CD&email=correo@ejemplo.com
    """
    try:
        pin = request.args.get("pin")
        id_partida = request.args.get("id_partida", type=int)
        email = request.args.get("email")
        
        # Validar que se proporcione el correo
        if not email:
            return jsonify({"ok": False, "msg": "Debe proporcionar un correo electrónico (parámetro 'email')"}), 400

        from controladores import controlador_partidas as c_part
        from controladores.google_drive_uploader import GoogleDriveUploader
        
        # Obtener datos completos del reporte
        if pin:
            data = c_part.reporte_por_pin(pin)
        elif id_partida:
            data = c_part.reporte_por_partida_id(id_partida)
        else:
            return jsonify({"ok": False, "msg": "Proporcione pin o id_partida"}), 400

        if not data:
            return jsonify({"ok": False, "msg": "Partida no encontrada"}), 404

        # Crear libro Excel (mismo código que export)
        wb = Workbook()
        wb.remove(wb.active)

        # --- HOJA 1: RESUMEN (Ranking Final) ---
        ws_resumen = wb.create_sheet("Resumen")
        ws_resumen.append(["Posición", "Usuario/Grupo", "PuntajeTotal", "RespuestasCorrectas", 
                          "RespuestasIncorrectas", "%Acierto", "TiempoPromedioResp (s)"])
        
        for cell in ws_resumen[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for idx, part in enumerate(data['participantes'], start=1):
            total_resp = int(part['correctas']) + int(part['incorrectas'])
            pct_acierto = round((int(part['correctas']) / total_resp * 100), 2) if total_resp > 0 else 0
            ws_resumen.append([
                idx,
                part['nombre'],
                int(part['puntaje_total']),
                int(part['correctas']),
                int(part['incorrectas']),
                pct_acierto,
                round(float(part['tiempo_prom_seg'] or 0), 2)
            ])

        # --- HOJA 2: DETALLE POR PARTICIPANTE ---
        ws_detalle_part = wb.create_sheet("Detalle por participante")
        ws_detalle_part.append(["Usuario", "Grupo(opc)", "PreguntaN", "Correcta(0/1)", 
                                "TiempoRestante", "PuntosOtorgados", "PuntajeAcumulado"])
        
        for cell in ws_detalle_part[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT pa.nombre, pa.id_grupo, rp.id_pregunta, rp.es_correcta,
                           TIME_TO_SEC(rp.tiempo_respuesta) AS tiempo_seg, rp.puntaje,
                           (SELECT SUM(rp2.puntaje) 
                            FROM RESPUESTA_PARTICIPANTE rp2 
                            WHERE rp2.id_participante = rp.id_participante 
                            AND rp2.id_respuesta <= rp.id_respuesta) AS puntaje_acum
                    FROM RESPUESTA_PARTICIPANTE rp
                    JOIN PARTICIPANTE pa ON pa.id_participante = rp.id_participante
                    WHERE rp.id_partida=%s
                    ORDER BY pa.nombre, rp.id_pregunta
                """, (id_partida if id_partida else data['header']['id_partida'],))
                rows_part = c.fetchall()
                
                for r in rows_part:
                    ws_detalle_part.append([
                        r['nombre'],
                        r['id_grupo'] or "",
                        r['id_pregunta'],
                        int(r['es_correcta']),
                        int(r['tiempo_seg'] or 0),
                        int(r['puntaje']),
                        int(r['puntaje_acum'] or 0)
                    ])
        finally:
            cx.close()

        # --- HOJA 3: DETALLE POR PREGUNTA ---
        ws_detalle_preg = wb.create_sheet("Detalle por pregunta")
        ws_detalle_preg.append(["#Pregunta", "TextoPregunta", "Opción", "EsCorrecta(0/1)", 
                               "RespuestasRecibidas", "Aciertos", "%Aciertos", "TiempoPromedioRestante"])
        
        for cell in ws_detalle_preg[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT rp.id_pregunta, 
                           MIN(rp.pregunta_texto) AS pregunta_texto,
                           rp.opcion_texto,
                           MAX(rp.es_correcta) AS es_correcta,
                           COUNT(*) AS respuestas_recibidas,
                           SUM(rp.es_correcta) AS aciertos,
                           ROUND(AVG(TIME_TO_SEC(rp.tiempo_respuesta)), 2) AS tiempo_prom
                    FROM RESPUESTA_PARTICIPANTE rp
                    WHERE rp.id_partida=%s
                    GROUP BY rp.id_pregunta, rp.opcion_texto
                    ORDER BY rp.id_pregunta, rp.opcion_texto
                """, (id_partida if id_partida else data['header']['id_partida'],))
                rows_preg = c.fetchall()
                
                for r in rows_preg:
                    pct_aciertos = round((int(r['aciertos']) / int(r['respuestas_recibidas']) * 100), 2) if r['respuestas_recibidas'] > 0 else 0
                    ws_detalle_preg.append([
                        r['id_pregunta'],
                        r['pregunta_texto'],
                        r['opcion_texto'],
                        int(r['es_correcta']),
                        int(r['respuestas_recibidas']),
                        int(r['aciertos']),
                        pct_aciertos,
                        float(r['tiempo_prom'] or 0)
                    ])
        finally:
            cx.close()

        # Guardar en memoria
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Obtener contenido en bytes
        excel_bytes = output.getvalue()
        
        filename = f"DogeHoot_Reporte_{pin if pin else id_partida}.xlsx"
        
        # Inicializar uploader de Google Drive
        credentials_file = os.path.join(app.root_path, 'credentials.json')
        token_file = os.path.join(app.root_path, 'token_drive.json')
        
        uploader = GoogleDriveUploader(
            credentials_file=credentials_file,
            token_file=token_file
        )
        
        # Buscar o crear carpeta "DogeHoot Reportes"
        carpetas = uploader.listar_archivos(max_resultados=100)
        folder_id = None
        
        if carpetas['success']:
            for archivo in carpetas['files']:
                if archivo['name'] == 'DogeHoot Reportes' and archivo['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_id = archivo['id']
                    break
        
        # Si no existe la carpeta, crearla
        if not folder_id:
            resultado_carpeta = uploader.crear_carpeta('DogeHoot Reportes')
            if resultado_carpeta['success']:
                folder_id = resultado_carpeta['folder_id']
            else:
                return jsonify({
                    "ok": False, 
                    "msg": f"Error al crear carpeta: {resultado_carpeta['message']}"
                }), 500
        
        # Subir archivo desde memoria
        resultado = uploader.subir_desde_memoria(
            contenido=excel_bytes,
            nombre_archivo=filename,
            mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            folder_id=folder_id
        )
        
        if not resultado['success']:
            return jsonify({
                "ok": False,
                "msg": f"Error al subir a Drive: {resultado['message']}"
            }), 500
        
        # Compartir el archivo con el correo proporcionado
        file_id = resultado['file_id']
        resultado_compartir = uploader.compartir_archivo(
            file_id=file_id,
            email=email,
            role='reader',  # Solo lectura
            tipo='user'
        )
        
        if resultado_compartir['success']:
            return jsonify({
                "ok": True,
                "msg": f"Reporte subido y compartido exitosamente con {email}",
                "file_name": resultado['file_name'],
                "file_id": resultado['file_id'],
                "web_view_link": resultado['web_view_link'],
                "download_link": resultado.get('download_link'),
                "shared_with": email
            }), 200
        else:
            # El archivo se subió pero no se pudo compartir
            return jsonify({
                "ok": True,
                "msg": f"Reporte subido pero hubo un error al compartir: {resultado_compartir['message']}",
                "file_name": resultado['file_name'],
                "file_id": resultado['file_id'],
                "web_view_link": resultado['web_view_link'],
                "download_link": resultado.get('download_link'),
                "warning": "No se pudo compartir con el correo especificado"
            }), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route('/api/report/partida/export-onedrive', methods=['GET'])
def api_report_partida_export_onedrive():
    """
    Genera Excel y lo sube a OneDrive en la carpeta 'DogeHoot/Reportes' y lo comparte con un correo
    
    Uso: 
    - /api/report/partida/export-onedrive?pin=AB12CD&email=correo@ejemplo.com
    - /api/report/partida/export-onedrive?id_partida=123&email=correo@ejemplo.com
    """
    try:
        pin = request.args.get('pin')
        id_partida = request.args.get('id_partida', type=int)
        email = request.args.get('email')
        
        # Validar que se proporcione el correo
        if not email:
            return jsonify({"ok": False, "msg": "Debe proporcionar un correo electrónico (parámetro 'email')"}), 400
        
        # Importar el uploader de OneDrive
        from controladores.onedrive_uploader import OneDriveUploader
        
        # === PASO 1: Obtener datos del reporte (igual que Google Drive) ===
        from controladores import controlador_partidas as c_part
        
        if pin:
            data = c_part.reporte_por_pin(pin)
        elif id_partida:
            data = c_part.reporte_por_partida_id(id_partida)
        else:
            return jsonify({"ok": False, "msg": "Proporcione pin o id_partida"}), 400
        
        if not data:
            return jsonify({"ok": False, "msg": "Partida no encontrada"}), 404
        
        # === PASO 2: Crear el archivo Excel (mismo código que ya tienes) ===
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        import io
        
        wb = Workbook()
        wb.remove(wb.active)  # Eliminar hoja por defecto
        
        # --- HOJA 1: RESUMEN ---
        ws_resumen = wb.create_sheet("Resumen")
        ws_resumen.append(['Posición', 'Usuario/Grupo', 'Puntaje Total', 'Respuestas Correctas', 
                          'Respuestas Incorrectas', '% Acierto', 'Tiempo Promedio (seg)'])
        
        # Estilo del header
        for cell in ws_resumen[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        # Llenar datos
        for idx, part in enumerate(data['participantes'], start=1):
            total_resp = int(part['correctas']) + int(part['incorrectas'])
            pct_acierto = round(int(part['correctas']) / total_resp * 100, 2) if total_resp > 0 else 0
            ws_resumen.append([
                idx,
                part['nombre'],
                int(part['puntaje_total']),
                int(part['correctas']),
                int(part['incorrectas']),
                pct_acierto,
                round(float(part['tiempo_prom_seg'] or 0), 2)
            ])
        
        # --- HOJA 2: DETALLE POR PARTICIPANTE ---
        ws_detalle_part = wb.create_sheet("Detalle por participante")
        ws_detalle_part.append(['Usuario', 'Grupo', 'Pregunta N°', 'Correcta (0/1)', 
                               'Tiempo Restante', 'Puntos Otorgados', 'Puntaje Acumulado'])
        
        for cell in ws_detalle_part[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        # Obtener detalle de respuestas
        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT pa.nombre, pa.id_grupo, rp.id_pregunta, rp.es_correcta,
                           TIME_TO_SEC(rp.tiempo_respuesta) AS tiempo_seg,
                           rp.puntaje,
                           (SELECT SUM(rp2.puntaje) FROM RESPUESTA_PARTICIPANTE rp2
                            WHERE rp2.id_participante = rp.id_participante 
                            AND rp2.id_respuesta <= rp.id_respuesta) AS puntaje_acum
                    FROM RESPUESTA_PARTICIPANTE rp
                    JOIN PARTICIPANTE pa ON pa.id_participante = rp.id_participante
                    WHERE rp.id_partida = %s
                    ORDER BY pa.nombre, rp.id_pregunta
                """, (id_partida if id_partida else data['header']['id_partida'],))
                rows_part = c.fetchall()
                
                for r in rows_part:
                    ws_detalle_part.append([
                        r['nombre'],
                        r['id_grupo'] or '',
                        r['id_pregunta'],
                        int(r['es_correcta']),
                        int(r['tiempo_seg'] or 0),
                        int(r['puntaje']),
                        int(r['puntaje_acum'] or 0)
                    ])
        finally:
            cx.close()
        
        # --- HOJA 3: DETALLE POR PREGUNTA ---
        ws_detalle_preg = wb.create_sheet("Detalle por pregunta")
        ws_detalle_preg.append(['Pregunta', 'Texto Pregunta', 'Opción', 'Es Correcta (0/1)',
                               'Respuestas Recibidas', 'Aciertos', '% Aciertos', 'Tiempo Promedio'])
        
        for cell in ws_detalle_preg[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        cx = obtener_conexion()
        try:
            with cx.cursor(pymysql.cursors.DictCursor) as c:
                c.execute("""
                    SELECT rp.id_pregunta, MIN(rp.pregunta_texto) AS pregunta_texto,
                           rp.opcion_texto, MAX(rp.es_correcta) AS es_correcta,
                           COUNT(*) AS respuestas_recibidas,
                           SUM(rp.es_correcta) AS aciertos,
                           ROUND(AVG(TIME_TO_SEC(rp.tiempo_respuesta)), 2) AS tiempo_prom
                    FROM RESPUESTA_PARTICIPANTE rp
                    WHERE rp.id_partida = %s
                    GROUP BY rp.id_pregunta, rp.opcion_texto
                    ORDER BY rp.id_pregunta, rp.opcion_texto
                """, (id_partida if id_partida else data['header']['id_partida'],))
                rows_preg = c.fetchall()
                
                for r in rows_preg:
                    pct_aciertos = round(int(r['aciertos']) / int(r['respuestas_recibidas']) * 100, 2) if r['respuestas_recibidas'] > 0 else 0
                    ws_detalle_preg.append([
                        r['id_pregunta'],
                        r['pregunta_texto'],
                        r['opcion_texto'],
                        int(r['es_correcta']),
                        int(r['respuestas_recibidas']),
                        int(r['aciertos']),
                        pct_aciertos,
                        float(r['tiempo_prom'] or 0)
                    ])
        finally:
            cx.close()
        
        # === PASO 3: Guardar Excel en memoria (bytes) ===
        output = io.BytesIO()
        wb.save(output)
        excel_bytes = output.getvalue()
        
        # Nombre del archivo
        filename = f'DogeHoot_Reporte_{pin if pin else id_partida}.xlsx'
        
        # === PASO 4: Subir a OneDrive ===
        uploader = OneDriveUploader()
        
        # Subir el archivo desde memoria a la carpeta DogeHoot/Reportes
        resultado = uploader.subir_desde_memoria(
            excel_bytes,
            filename,
            folder_path='DogeHoot/Reportes'
        )
        
        if not resultado['success']:
            return jsonify({
                'ok': False,
                'msg': f'Error al subir a OneDrive: {resultado["message"]}'
            }), 500
        
        # === PASO 5: Compartir el archivo con el correo proporcionado ===
        file_id = resultado['file_id']
        resultado_compartir = uploader.compartir_archivo(
            file_id=file_id,
            email=email,
            role='read',  # Solo lectura
            send_notification=True  # Enviar notificación por correo
        )
        
        if resultado_compartir['success']:
            return jsonify({
                'ok': True,
                'msg': f'Reporte subido y compartido exitosamente con {email}',
                'file_name': resultado['file_name'],
                'file_id': resultado['file_id'],
                'web_url': resultado['web_url'],  # URL para ver el archivo en OneDrive
                'download_url': resultado.get('download_url'),  # URL de descarga directa
                'shared_with': email
            }), 200
        else:
            # El archivo se subió pero no se pudo compartir
            return jsonify({
                'ok': True,
                'msg': f'Reporte subido pero hubo un error al compartir: {resultado_compartir["message"]}',
                'file_name': resultado['file_name'],
                'file_id': resultado['file_id'],
                'web_url': resultado['web_url'],
                'download_url': resultado.get('download_url'),
                'warning': 'No se pudo compartir con el correo especificado'
            }), 200
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500


# ============================================
# RUTAS PARA ONEDRIVE OAuth
# ============================================

@app.route('/onedrive/auth')
def onedrive_auth():
    """Inicia el proceso de autenticación con OneDrive"""
    uploader = OneDriveUploader()
    auth_url = uploader.get_authorization_url()
    return redirect(auth_url)


@app.route('/onedrive/callback', methods=['GET', 'POST'])
def onedrive_callback():
    """Callback de OneDrive después de la autenticación"""
    # Obtener todos los parámetros para debugging
    all_params = dict(request.args)
    all_form = dict(request.form) if request.form else {}
    
    print("="*50)
    print(f"Método de petición: {request.method}")
    print(f"URL completa: {request.url}")
    print(f"Query params (GET): {all_params}")
    print(f"Form data (POST): {all_form}")
    print(f"Headers: {dict(request.headers)}")
    print("="*50)
    
    # Intentar obtener el código de GET o POST
    code = request.args.get('code') or request.form.get('code')
    error = request.args.get('error') or request.form.get('error')
    error_description = request.args.get('error_description') or request.form.get('error_description')
    
    if error:
        return jsonify({
            'success': False,
            'message': f'Error en autenticación: {error}',
            'error_description': error_description,
            'params_received': all_params,
            'form_received': all_form
        }), 400
    
    if code:
        print(f"✓ Código recibido: {code[:20]}...")
        uploader = OneDriveUploader()
        result = uploader.exchange_code_for_tokens(code)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'OneDrive conectado exitosamente. Ya puedes subir archivos.'
            })
        else:
            return jsonify(result), 400
    
    # Si no hay código ni error, mostrar qué se recibió
    return jsonify({
        'success': False,
        'message': 'No se recibió código de autenticación',
        'params_received': all_params,
        'form_received': all_form,
        'url_received': request.url
    }), 400


@app.route('/onedrive/test-upload')
def onedrive_test_upload():
    """Ruta de prueba para subir un archivo a OneDrive"""
    try:
        uploader = OneDriveUploader()
        
        # Crear un archivo de prueba
        test_content = b"Este es un archivo de prueba de DogeHoot"
        result = uploader.subir_desde_memoria(
            test_content,
            'prueba_dogehoot.txt',
            folder_path='DogeHoot/Pruebas'
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
