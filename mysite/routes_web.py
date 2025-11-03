from flask import g, render_template, request, redirect, url_for, flash, session, jsonify, abort
from main import app, mail
from flask_mail import Message
from flask_login import login_required, current_user

from controladores import usuarios as ctrl_usuarios
from controladores import cuestionarios as cc
from controladores import preguntas_opciones as cpo
from controladores import categorias as ctrl_cat
from controladores import outlook_email_sender as email_sender
from controladores import controlador_skins as ctrl_skins
from controladores import controlador_partidas as ctrl_partidas
# ------------------------------------------------------------------------------
# PAGINAS PUBLICAS Y DE AUTENTICACIÓN


@app.route("/")
def inicio():
    if 'user_id' not in session:
        # flash('Debes iniciar sesión para ver esta página.', 'warning')
        return redirect(url_for("auth"))

    return redirect(url_for("dashboard"))

# @app.route("/auth", methods=["GET", "POST"])
# def auth():
#     if request.method == "GET":
#         return render_template("index.html")
#     if "correologin" in request.form and "contrasenaLogin" in request.form:
#         correo = request.form.get("correologin", "").strip()
#         contrasena = request.form.get("contrasenaLogin", "").strip()

#         usuario = ctrl_usuarios.validar_credenciales(correo, contrasena)

#         if usuario:
#             session["user_id"] = usuario["id_usuario"]
#             session["nombre_usuario"] = usuario["nombre_usuario"]
#             session["tipo_usuario"] = usuario["tipo"]
#             flash("¡Has iniciado sesión correctamente!", "success")
#             return redirect(url_for("dashboard"))
#         else:
#             flash("Correo o contraseña incorrectos. Inténtalo de nuevo.", "danger")
#             return redirect(url_for("auth"))
#     elif "nombre" in request.form and "correo" in request.form and "contrasena" in request.form:
#         nombre_completo = request.form.get("nombre", "").strip()
#         nombre_usuario = request.form.get("usuario", "").strip()
#         correo = request.form.get("correo", "").strip()
#         contrasena = request.form.get("contrasena", "").strip()
#         tipo_cuenta_form = request.form.get("tipoCuenta", "Estudiante").strip()

#         tipo_cuenta_db = "P" if tipo_cuenta_form == "Profesor" else "E"

#         exito, mensaje = ctrl_usuarios.crear_usuario(
#             nombre_completo,
#             nombre_usuario,
#             correo,
#             contrasena,
#             tipo_cuenta_db
#         )

#         if exito:
#             flash(mensaje, "success")
#             return redirect(url_for("auth"))  # vuelve al mismo y se queda en login
#         else:
#             flash(mensaje, "danger")
#             return redirect(url_for("auth"))
#     else:
#         flash("Solicitud no válida.", "warning")
#         return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == 'POST':

        # --- LÓGICA DE LOGIN (Esta parte está bien) ---
        if "correologin" in request.form:
            correo = request.form.get("correologin", "").strip()
            contrasena = request.form.get("contrasenaLogin", "").strip()

            err = False
            if len(correo) > 100:
                flash("Longitud de correo no válida [Max 100]", "danger")
                err = True
            if len(contrasena) > 50:
                flash("Longitud de contraseña no válida [Max 50]", "danger")
                err = True

            if err:
                return render_template("index.html")

            usuario = ctrl_usuarios.validar_credenciales(correo, contrasena)

            if usuario:
                session["user_id"] = usuario["id_usuario"]
                session["nombre_usuario"] = usuario["nombre_usuario"]
                session["tipo_usuario"] = usuario["tipo"]
                #flash("¡Has iniciado sesión correctamente!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("El correo o contraseña son incorrectos o la cuenta no está vigente.", "danger")
                return redirect(url_for("auth"))

        # --- LÓGICA DE REGISTRO (¡AQUÍ ESTÁ LA CORRECCIÓN!) ---
        # ===== CAMBIO AQUÍ: Buscamos "nombre" en lugar de "nombre_completo" =====
        elif "nombre" in request.form:
            # Ahora usamos los 'name' exactos de tu index.html
            nombre_completo = request.form.get("nombre", "").strip()
            nombre_usuario = request.form.get("usuario", "").strip()
            correo = request.form.get("correo", "").strip()
            contrasena = request.form.get("contrasena", "").strip()
            tipo_cuenta_form = request.form.get("tipoCuenta", "Estudiante").strip()
            tipo_cuenta_db = "P" if tipo_cuenta_form == "Profesor" else "E"

            err = False
            if len(nombre_completo) > 150:
                flash("Longitud de nombre no válida [Max 150]", "danger")
                err = True
            if len(nombre_usuario) > 18:
                flash("Longitud de nombre de usuario [Max 18] no válida", "danger")
                err = True
            if len(correo) > 100:
                flash("Longitud de correo no válida [Max 100]", "danger")
                err = True
            if len(contrasena) > 50:
                flash("Longitud de contraseña no válida [Max 50]", "danger")
                err = True

            if err:
                return render_template("index.html")

            try:
                # 1. Intentamos crear el usuario como "pendiente"
                exito, resultado = ctrl_usuarios.crear_usuario_pendiente(
                    nombre_completo, nombre_usuario, correo, contrasena, tipo_cuenta_db
                )

                if exito:
                    codigo_verificacion = resultado

                    # ===== ¡CAMBIO FINAL AQUÍ! =====
                    # Llamamos al nuevo controlador que usa la API de Outlook/Microsoft Graph
                    enviado, mensaje_email = email_sender.enviar_correo_verificacion(correo, codigo_verificacion)

                    if enviado:
                        flash('Registro casi listo. Te enviamos un código a tu correo para activar tu cuenta.', 'info')
                        return redirect(url_for('verificar', email=correo))
                    else:
                        # Si la API falla, mostramos el error
                        flash(f'No se pudo enviar el correo de verificación. Error: {mensaje_email}', 'danger')
                        return redirect(url_for('verificar',email=correo))

                else:
                    flash(resultado, "danger")


            except Exception as e:
                import traceback
                print(f"❌ ERROR EN REGISTRO: {str(e)}")
                traceback.print_exc()
                flash(f"Ha ocurrido un error con el registro: {str(e)}", "danger")



    # Si es un GET o falla la lógica de POST, muestra la página principal
    return render_template("index.html")


# --- RUTA PARA LA PÁGINA DE VERIFICACIÓN ---
# @app.route('/verificar', methods=['GET', 'POST'])
# def verificar():
#     email = request.args.get('email')
#     # if not email:
#     #     return redirect(url_for('auth'))

#     valido = ctrl_usuarios.esta_pendiente_de_verificacion(email)

#     if not valido:
#         flash('Correo no válido para activar\nUsuario no encontrado o ya ha sido verificado','danger')
#         #return render_template('verificar.html', email=email, valido=valido)

#     if request.method == 'POST':
#         codigo = request.form.get('codigo')
#         email_form = request.form.get('email')
#         resultado = ctrl_usuarios.verificar_y_activar_usuario(email_form, codigo)

#         if resultado == "OK":
#             flash('¡Cuenta verificada! Ahora puedes iniciar sesión.', 'success')
#             return redirect(url_for('auth')) # Lo mandamos de vuelta a /auth para que inicie sesión
#         else:
#             flash(resultado, 'danger')
#             return redirect(url_for('verificar', email=email_form))

#     return render_template('verificar.html', email=email, valido = valido)


# ------------------------

# @app.route('/verificar', methods=['GET', 'POST'])
# def verificar():
#     email = request.args.get('email')
#     # Esta verificación sí es importante, por si alguien llega sin un correo en la URL
#     # if not email:
#     #   return redirect(url_for('auth'))

#     # --- Lógica para el método POST (cuando se envía el formulario) ---
#     if request.method == 'POST':
#         codigo = request.form.get('codigo')
#         email_form = request.form.get('email')
#         resultado = ctrl_usuarios.verificar_y_activar_usuario(email_form, codigo)

#         if resultado == "OK":
#             flash('¡Cuenta verificada! Ahora puedes iniciar sesión.', 'success')
#             return redirect(url_for('auth'))
#         else:
#             flash(resultado, 'danger')
#             return redirect(url_for('verificar', email=email_form))

#     # --- Lógica para el método GET (cuando se carga la página) ---
#     # Simplemente mostramos la página. La validación real se hará en el POST.
#     # Ya no necesitamos la variable 'valido'.
#     return render_template('verificar.html', email=email)

@app.route('/verificar', methods=['GET', 'POST'])
def verificar():
    email = request.args.get('email')
    # if not email:
    #     return redirect(url_for('auth'))
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        email_form = request.form.get('email')
        resultado = ctrl_usuarios.verificar_y_activar_usuario(email_form, codigo)
        if resultado == "OK":
            flash('¡Cuenta verificada! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth')) # Lo mandamos de vuelta a /auth para que inicie sesión
        else:
            flash(resultado, 'danger')
            return redirect(url_for('verificar', email=email_form))


    valido = ctrl_usuarios.esta_pendiente_de_verificacion(email)
    if not valido:
        flash('Correo no válido para activar\nUsuario no encontrado o ya ha sido verificado','danger')
        return render_template('verificar.html', email=email, valido=valido)

    return render_template('verificar.html', email=email, valido = valido)



@app.route('/verificar/reenviar', methods=['POST'])
def reenviar_codigo():
    email = request.form.get('email')
    if not email:
        return redirect(url_for('auth'))

    # 1. Llama al controlador para generar un nuevo código
    exito, resultado = ctrl_usuarios.regenerar_codigo(email)

    if exito:
        nuevo_codigo = resultado
        try:
            # 2. Llama a la función de envío de correo, ahora SIN la URL
            enviado, mensaje_email = email_sender.enviar_correo_codigo_nuevo(email, nuevo_codigo)

            if enviado:
                flash('Te hemos reenviado un nuevo código de verificación a tu correo.', 'info')
            else:
                flash(f'No se pudo reenviar el correo. Error: {mensaje_email}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error al intentar reenviar el correo: {e}', 'danger')
    else:
        # Si el controlador devuelve un error (ej: usuario no encontrado), lo mostramos
        flash(resultado, 'danger')

    # 3. Redirige de vuelta a la página de verificación para mostrar el mensaje
    return redirect(url_for('verificar', email=email))


@app.route('/logout')
def logout():
    session.clear()
    #flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth'))


# ------------------------------------------------------------------------------
# PANEL DEL PROFESOR


@app.route("/home")
def home():
    return "/home"


@app.route('/dashboard')
def dashboard():
    # 1. Verifica si el usuario ha iniciado sesión
    if 'user_id' not in session:
        # flash('Debes iniciar sesión para ver esta página.', 'warning')
        return redirect(url_for('auth')) # Redirige al login si no está en sesión

    # 2. Obtiene el ID del usuario de la sesión
    id_usuario_actual = session['user_id']

    # 3. Obtiene los cuestionarios MÁS JUGADOS (excluyendo los del usuario actual)
    cuestionarios_populares = cc.obtener_mas_jugados(limite=9, excluir_usuario=id_usuario_actual)

    # 4. Obtiene todas las categorías para el filtro
    categorias = ctrl_cat.obtener_todas()

    # 5. Pasa los datos a la plantilla
    return render_template(
        'dashboard.html',
        nombre_usuario=session['nombre_usuario'],
        tipo_usuario=session['tipo_usuario'],
        cuestionarios=cuestionarios_populares,
        categorias=categorias
    )


@app.route("/cuestionarios")
def cuestionarios():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver esta página.', 'warning')
        return redirect(url_for('auth')) # Redirige al login si no está en sesión

    id_usuario_actual = session['user_id']

    mis_cuestionarios = cc.obtener_con_filtros(id_usuario=id_usuario_actual)

    return render_template(
        "cuestionarios.html",
        nombre_usuario=session['nombre_usuario'],
        tipo_usuario=session['tipo_usuario'],
        cuestionarios=mis_cuestionarios
    )



@app.route("/cuestionarios/nuevo")
def cuestionarios_nuevo():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para crear un cuestionario.', 'warning')
        return redirect(url_for('auth'))

    categorias = ctrl_cat.obtener_todas()

    return render_template(
        'mantenimiento_cuestionario.html',
        nombre_usuario=session.get('nombre_usuario'), # Usamos .get() por seguridad
        tipo_usuario=session['tipo_usuario'],
        cuestionario_data=None, # Indicador de que es nuevo
        categorias=categorias,
        modo='nuevo'
    )



@app.route('/cuestionarios/<int:id_cuestionario>/editar')
def cuestionarios_editar(id_cuestionario):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para editar.', 'warning')
        return redirect(url_for('login'))

    cuestionario_completo = cc.obtener_completo_por_id(id_cuestionario)

    if not cuestionario_completo:
        flash('El cuestionario no existe.', 'danger')
        return redirect(url_for('cuestionarios'))

    categorias = ctrl_cat.obtener_todas()

    return render_template(
        'mantenimiento_cuestionario.html',
        nombre_usuario=session.get('nombre_usuario'),
        tipo_usuario=session['tipo_usuario'],
        cuestionario_data=cuestionario_completo, # Pasa el diccionario Python
        categorias=categorias
    )



@app.route("/cuestionarios/explorar")
def cuestionarios_explorar():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    id_usuario_actual = session['user_id']
    
    # Obtener todos los cuestionarios públicos (excluyendo los del usuario)
    todos_cuestionarios = cc.obtener_publicos(excluir_usuario=id_usuario_actual)
    
    # Obtener categorías para filtros
    categorias = ctrl_cat.obtener_todas()
    
    return render_template(
        'explorar.html',
        nombre_usuario=session['nombre_usuario'],
        tipo_usuario=session['tipo_usuario'],
        cuestionarios=todos_cuestionarios,
        categorias=categorias
    )


@app.route("/reportes")


@app.route('/cuestionarios/clonar/<int:id_cuestionario>', methods=['POST'])
def clonar_cuestionario(id_cuestionario):
    """Clona un cuestionario público para el usuario actual"""
    print(f"[DEBUG CLONAR] Ruta llamada con id_cuestionario={id_cuestionario}")
    print(f"[DEBUG CLONAR] Método: {request.method}")
    print(f"[DEBUG CLONAR] Session: {session.get('user_id')}")
    
    if 'user_id' not in session:
        flash('Debes iniciar sesión para clonar cuestionarios.', 'warning')
        return redirect(url_for('auth'))
    
    id_usuario = session['user_id']
    print(f"[DEBUG CLONAR] ID Usuario: {id_usuario}")
    
    # Llamar al controlador para clonar
    exito, resultado = cc.clonar_cuestionario(id_cuestionario, id_usuario)
    
    print(f"[DEBUG CLONAR] Resultado: exito={exito}, resultado={resultado}")
    
    if exito:
        flash(f'¡Cuestionario clonado exitosamente! Ahora puedes editarlo en "Mis Cuestionarios".', 'success')
        return redirect(url_for('cuestionarios'))
    else:
        flash(resultado, 'danger')
        return redirect(url_for('dashboard'))


@app.route("/reportes", methods=['GET', 'POST'])
def reportes():
    return "/reportes"


@app.route("/reportes/<int:id_partida>")
def reportes_detalle(id_partida):
    return "/reportes/<int:id_partida>"


@app.route('/mis-partidas')
def mis_partidas():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus partidas.', 'warning')
        return redirect(url_for('auth'))

    # Obtenemos el ID del usuario de la sesión
    id_usuario_actual = session['user_id']

    # Llamamos al controlador para obtener la lista de partidas
    lista_de_partidas = ctrl_partidas.obtener_partidas_por_usuario(id_usuario_actual)

    return render_template('mis_partidas.html',
                            nombre_usuario=session.get('nombre_usuario'),
                            tipo_usuario=session['tipo_usuario'],
                            partidas=lista_de_partidas
    )

# ------------------------------------------------------------------------------
# PANEL DEL USUARIO EN GENERAL


@app.route("/usuario/perfil")
def usuario_perfil():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu perfil.', 'warning')
        return redirect(url_for('auth'))

    user = g.user or {}  # ya lo cargó before_request
    stats = {
        'puntos_actuales': user.get('puntos', 0),
        'meta_puntos': 1000, # Puedes hacer esto dinámico más adelante
        'porcentaje_puntos': (user.get('puntos', 0) / 1000) * 100,
        'monedas': user.get('monedas', 0)
    }

    return render_template(
        'perfil.html',
        user=user,
        objetivo_puntos=20000,
        objetivo_monedas=5000,
        stats=stats # Pasamos el nuevo objeto a la plantilla
    )

@app.before_request
def load_logged_in_user():
    uid = session.get("user_id")
    g.user = None
    if uid:
        u = ctrl_usuarios.obtener_por_id(uid)
        if u:
            u.pop("contraseña", None)   # nunca expongas el hash
            g.user = u

@app.context_processor
def inject_user():
    u = getattr(g, "user", {}) or {}
    # calcula primer nombre seguro
    first = "Usuario"
    try:
        if u.get("nombre_completo"):
            first = str(u["nombre_completo"]).strip().split()[0]
    except Exception:
        pass
    return {
        "user": u,
        "first_name": first,
        "objetivo_puntos": 20000,
        "objetivo_monedas": 5000,
    }

@app.route("/usuario/perfil/actualizar", methods=["POST"])
def perfil_update():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    data = request.json
    id_usuario = session['user_id']
    nombre_completo = data.get('nombre_completo')

    # ===== CAMBIO AQUÍ: Ahora esperamos 'nombre_usuario' directamente =====
    nombre_usuario = data.get('nombre_usuario')

    exito, mensaje = ctrl_usuarios.actualizar_perfil(id_usuario, nombre_completo, nombre_usuario)

    if exito:
        # Esto es CLAVE: actualizamos el nombre en la sesión
        session['nombre_usuario'] = nombre_usuario
        # Devolvemos el usuario actualizado para que el frontend lo pueda usar
        usuario_actualizado = ctrl_usuarios.obtener_por_id(id_usuario)
        return jsonify(usuario_actualizado), 200
    else:
        return jsonify({"error": mensaje}), 400

# Cambio de contraseña ->Comentar
#@app.route("/usuario/perfil/cambiar_password", methods=["POST"])
#def perfil_change_password():
#    if 'user_id' not in session:
#        return jsonify({"error": "No autorizado"}), 401

#    data = request.get_json(force=True) or {}
#    pwd_actual = (data.get("actual") or "").strip()
#    pwd_nueva  = (data.get("nueva")  or "").strip()

 #   if not pwd_actual or not pwd_nueva:
 #       return jsonify({"error": "Faltan datos"}), 400

    # Traer usuario con HASH
 #   u = ctrl_usuarios.obtener_por_id_con_hash(session['user_id'])
 #  if not u:
 #       return jsonify({"error": "Usuario no encontrado"}), 404

    # Contraseña actual incorrecta
 #   if not check_password_hash(u["contraseña"], pwd_actual):
  #      return jsonify({"error": "Tu contraseña actual no es la correcta"}), 409

    # Actualizar contraseña
   # nuevo_hash = generate_password_hash(pwd_nueva)
#    ok = ctrl_usuarios.actualizar_password(session['user_id'], nuevo_hash)

 #   if not ok:
  #      return jsonify({"error": "Algo salió mal, vuelve a intentarlo"}), 500

   # return jsonify({"ok": True}), 200

@app.route("/usuario/perfil/cambiar-contrasena", methods=["GET"])
def pagina_cambiar_contrasena():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver esta página.', 'warning')
        return redirect(url_for('auth'))
    return render_template('cambio_contrasenia.html')

@app.route("/perfil/eliminar_cuenta")
def eliminar_cuenta():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu perfil.', 'warning')
        return redirect(url_for('auth'))

    user = g.user or {}  # ya lo cargó before_request

    return render_template("eliminar_cuenta.html", user=user)

#@app.route("/usuario/perfil/update", methods=["POST"])
#def usuario_perfil_update():
#    if 'user_id' not in session:
#        return jsonify({"ok": False, "msg": "No autenticado"}), 401

#    data = request.get_json() or {}
#    ok, msg = ctrl_usuarios.actualizar_perfil(session['user_id'], data)  # ajusta a tu lógica
#    return (jsonify({"ok": True}), 200) if ok else (jsonify({"ok": False, "msg": msg}), 400)

# ------------------------------------------------------------------------------
# FLUJO DE JUEGO


@app.route("/jugar")
def jugar():
    return "/jugar"

@app.route('/partida/<int:id_cuestionario>')
def generar_partida(id_cuestionario):
    exito, resultado = ctrl_partidas.crear_partida(id_cuestionario)

    if exito:
        pin_de_juego = resultado
        # Redirige a la pantalla del lobby (proyector) con el PIN
        # return "salio bien" + resultado
        flash(f"Se creó la partida: {pin_de_juego}", 'success')
        return redirect(url_for('cuestionarios'))
    else:
        # Si falla (porque ya hay una partida activa), muestra el error
        flash(resultado, 'danger')
        #return "fallo" + resultado
        return redirect(url_for('cuestionarios'))

# ----

@app.route('/jugar/<int:id_cuestionario>')
def configurar_partida(id_cuestionario):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para crear una partida.', 'warning')
        return redirect(url_for('auth'))

    # Obtenemos los datos del cuestionario para mostrar su título
    cuestionario = cc.obtener_por_id(id_cuestionario)
    if not cuestionario:
        flash('El cuestionario no existe.', 'danger')
        return redirect(url_for('cuestionarios'))

    return render_template('partida/nueva_partida.html',
                            nombre_usuario=session.get('nombre_usuario'),
                            tipo_usuario=session['tipo_usuario'],
                            cuestionario=cuestionario
    )


@app.route('/partida/lanzar', methods=['POST'])
def lanzar_partida():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    # Obtenemos los datos del formulario
    id_cuestionario = request.form.get('id_cuestionario', type=int)
    modalidad = request.form.get('modalidad') # 'individual' o 'grupal'
    cant_grupos = request.form.get('cant_grupos', type=int)

    es_grupal = (modalidad == 'grupal')

    # Llamamos al controlador para crear la partida en la BD, pasando el ID del usuario que la lanza
    exito, resultado = ctrl_partidas.crear_partida(
        id_cuestionario, 
        es_grupal, 
        cant_grupos,
        id_usuario_anfitrion=session['user_id']  # Usuario que lanza la partida
    )

    if exito:
        pin_de_juego = resultado
        # flash(f"¡Partida lanzada con éxito! PIN: {pin_de_juego}", 'success')
        # Redirigimos al panel del anfitrión con el PIN generado
        return redirect(url_for('partida_panel', pin=pin_de_juego))
    else:
        # Si falla (ej: ya hay una partida activa), mostramos el error
        flash(resultado, 'danger')
        return redirect(url_for('cuestionarios'))


@app.route("/partida/<string:pin>/panel_anfitrion")
def partida_panel(pin):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    partida = ctrl_partidas.obtener_partida_por_pin(pin)
    if not partida:
        flash('La partida indicada no existe.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template(
        'partida/panel_anfitrion.html',
        pin=pin,
        id_partida=partida.get('id_partida'),
    )

# -----------

@app.route('/lobby/<string:pin>')
def lobby(pin):
    if 'user_id' not in session:
        # Podrías permitir invitados, pero por ahora requerimos sesión
        return redirect(url_for('auth'))

    # Verificar que la partida existe y no está finalizada
    partida = ctrl_partidas.obtener_partida_por_pin(pin)
    if not partida:
        flash('El código de sesión no es válido.', 'danger')
        return redirect(url_for('dashboard'))
    
    if partida.get('estado') == 'FINALIZADA':
        flash('Esta partida ya ha finalizado. No puedes unirte.', 'warning')
        return redirect(url_for('dashboard'))

    return render_template('partida/lobby_participante.html', pin=pin)
    # return render_template('juego_participante.html', pin=pin)
    # return render_template('lobby_seleccion.html', pin=pin)



# routes_web.py
@app.route('/juego/<string:pin>')
def pagina_juego(pin):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    return render_template('partida/juego_participante.html', pin=pin)

@app.route("/partida/<int:id_partida>/juego")
def partida_juego(pin):
    return "/lobby/<str:pin>"


@app.route("/partida/<int:id_partida>/proyectar")
def partida_proyectar(id_partida):
    return "/partida/<int:id_partida>/proyectar"


@app.route("/partida/resultados")
def partida_resultados():
    return "/partida/resultados"


# ------------------------------------------------------------------------------
# PANEL DE ADMINISTRACION


@app.route("/admin/usuarios")
def admin_usuarios():
    return "/admin/usuarios"


@app.route("/admin/categorias")
def admin_categorias():
    return "/partida/resultados"


@app.route("/admin/skins")
def admin_skins():
    return "/admin/skins"


# ------------------------------------------------------------------------------
# TIENDA DE SKINS
# ------------------------------------------------------------------------------

@app.route("/tienda/skins")
def tienda_skins():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a la tienda.', 'warning')
        return redirect(url_for('auth'))

    id_usuario = session['user_id']
    user = ctrl_usuarios.obtener_por_id(id_usuario) or {}

    # Todas las skins disponibles
    skins_disponibles = ctrl_skins.obtener_todas() or []

    # Skins que ya tiene el usuario
    skins_usuario = ctrl_skins.obtener_por_usuario(id_usuario) or []

    # Marcar cuáles ya posee el usuario
    ids_mis_skins = {s['id_skin'] for s in skins_usuario}
    for s in skins_disponibles:
        s['ya_comprada'] = s['id_skin'] in ids_mis_skins


    return render_template(
        "skins.html",
        user=user,
        skins=skins_disponibles,
    )



# --- API para comprar skin ---
@app.route("/api/skins/comprar/<int:id_skin>", methods=["POST"])
def api_comprar_skin(id_skin):
    if 'user_id' not in session:
        return jsonify({"error": "Debes iniciar sesión."}), 401

    id_usuario = session['user_id']

    # Por ahora definimos un costo fijo por skin (puedes hacerlo dinámico)
    costo_skin = 100

    exito, mensaje = ctrl_skins.comprar_skin(id_usuario, id_skin, costo_skin)

    if exito:
        return jsonify({"mensaje": mensaje}), 200
    else:
        return jsonify({"error": mensaje}), 400

# --- MIS SKINS (las que el usuario ya posee) ---
@app.route("/usuario/skins")
def mis_skins():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus skins.', 'warning')
        return redirect(url_for('auth'))

    id_usuario = session['user_id']
    user = ctrl_usuarios.obtener_por_id(id_usuario)
    skins_usuario = ctrl_skins.obtener_por_usuario(id_usuario)


    return render_template(
        "mis_skins.html",
        user=user,
        skins=skins_usuario,
    )

@app.route("/api/skins/cambiar/<int:id_skin>", methods=["POST"])
def cambiar_skin(id_skin):
    id_usuario = session.get('user_id')
    if not id_usuario:
        return jsonify({"error": "No autorizado"}), 401

    ok, mensaje = ctrl_skins.cambiar_skin_activa(id_usuario, id_skin)
    if ok:
        # Actualizamos g.user y la sesión para que la plantilla sepa la skin activa
        skin_activa = ctrl_skins.obtener_por_usuario(id_usuario)
        ruta = next((s['ruta'] for s in skin_activa if s['id_skin'] == id_skin), None)
        g.user['skin_ruta'] = ruta

        return jsonify({"mensaje": mensaje, "ruta": ruta})
    else:
        return jsonify({"error": mensaje}), 400
    
@app.route("/api/skins/quitar", methods=["POST"])
def quitar_skin():
    id_usuario = session.get('user_id')
    if not id_usuario:
        return jsonify({"error": "No autorizado"}), 401

    ok, mensaje = ctrl_skins.quitar_skin_activa(id_usuario)
    if ok:
        g.user['skin_ruta'] = None  # Actualizamos la skin activa en sesión
        return jsonify({"mensaje": mensaje}), 200
    else:
        return jsonify({"error": mensaje}), 400


#-----------------CODIGO PARA ACCESO A SESION EN MODO VISUALIZACION V1---------------------

@app.route('/cuestionarios/<int:id_cuestionario>/visualizar')
def cuestionarios_visualizar(id_cuestionario):
    """Muestra el cuestionario en modo solo lectura para alumnos"""

    # Obtener el PIN de la URL para validación adicional (opcional)
    pin = request.args.get('pin', '')

    # Obtener el cuestionario completo
    cuestionario_completo = cc.obtener_completo_por_id(id_cuestionario)

    if not cuestionario_completo:
        flash('El cuestionario no existe.', 'danger')
        return redirect(url_for('cuestionarios'))

    # Obtener categorías (aunque no se editarán)
    categorias = ctrl_cat.obtener_todas()

    return render_template(
        'mantenimiento_cuestionario.html',
        nombre_usuario=session.get('nombre_usuario', 'Invitado'),
        tipo_usuario=session['tipo_usuario'],
        cuestionario_data=cuestionario_completo,
        categorias=categorias,
        modo_visualizacion=True,  # ¡CLAVE! Indica modo solo lectura
        pin_sesion=pin  # Por si quieres mostrarlo en la interfaz
    )

@app.route("/restablecer/<token>", methods=['GET', 'POST'])
def restablecer_con_token(token):
    id_usuario = ctrl_usuarios.verificar_token_restablecimiento(token)
    if id_usuario is None:
        flash('El enlace de restablecimiento es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth'))

    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not password or len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return render_template('restablecer_contrasena.html')

        if password != password2:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('restablecer_contrasena.html')

        # Guardamos la contraseña en texto plano
        ctrl_usuarios.actualizar_contrasena(id_usuario, password)

        flash('Tu contraseña ha sido actualizada con éxito. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth'))

    return render_template('restablecer_contrasena.html')

# ---------------------------------- AGREGADO POR PAME - Reportes
@app.route('/reportes/partida/<int:id_partida>')
def reporte_partida_page(id_partida):
    # Página HTML que consumirá el endpoint JSON /api/report/partida
    return render_template('reportes_partida.html', id_partida=id_partida)

# Para la pagina "guia.html"

@app.route("/guia")
def guia():
    pasos = [
        {
            "titulo": "1) Si eres profesor, Crea cuestionarios!!",
            "texto": "Primero, dirigete al panel de cuestionarios y crea uno nuevo dandole click en 'Agregar Cuestionario'. \nLlena los datos necesarios como el Titulo(1), Categoria(2), Descripcion(3),  y si deseas que otros profesores puedan ver tu cuestionario(4).\nPara agregar preguntas, puedes importar (sigue los pasos que se te indica) o puedes agregarlas manualmente. Finalmente, da click en 'Guardar Cambios'",
            
            "imagenes": [
                "https://drive.google.com/thumbnail?id=10ppj9ialb4H0w6iTzaSTC7POZMOTX4w6&sz=w1600",
                "https://drive.google.com/thumbnail?id=1mvnVYz4NXBV84AgUdVb6fCvhABowdvUj&sz=w1600",
                "https://drive.google.com/thumbnail?id=13mLknlovSbpMI2o-LAvA8twLlJGh7yjg&sz=w1600",
                "https://drive.google.com/thumbnail?id=16bludYRCMIzFYWo8aSCWowNcbuOwOBc_&sz=w1600",
                "https://drive.google.com/thumbnail?id=1hWTEg3HkyHCVg1pcf1nXgPiB6rusWmvI&sz=w1600",
            ],
        },
        {
            "titulo": "2) Si eres profesor, Inicia partida",
            "texto": "Dirigete nuevamente al panel de cuestionarios y selecciona el cuestionario y da click en 'Jugar'.\nConfigura la partida según corresponda y luego da click en 'Lanzar Partida'.\nComparte el PIN con tus estudiantes para que puedan unirse.",
            "imagenes": [
                "https://drive.google.com/thumbnail?id=1sqDqVRXRfBjnk5gX3WUYtA8iK5PyT3jt&sz=w1600",
                "https://drive.google.com/thumbnail?id=18h1oRKGRTWb-3yPu98cOh3blz7oJRY_l&sz=w1600",
                "https://drive.google.com/thumbnail?id=1iR5upHiXPUBXsoVgdwh18PlrkYg1DA6w&sz=w1600",
            ],
        },
        {
            "titulo": "3) Si eres estudiante o profesor puedes Unirte a una partida con PIN",
            "texto": "Dirigete al dashboard e ingresan el PIN de la partida en curso.\nEspera a que tu profesor inicie la partida.",
            "imagenes": [
                "https://drive.google.com/thumbnail?id=1-hnGdybQhPY0-qwOOAimBsHBuwcYtmP5&sz=w1600",
                "https://drive.google.com/thumbnail?id=189ONku0xfKgJR1eiJ9B7zSg4msjGSCDA&sz=w1600",
            ],
        },
        {
            "titulo": "4) Si eres profesor, Ve los resultados de tus partidas",
            "texto": "Cuando la partida haya finalizado, puedes darle click al botón 'Ver Reporte'.\nPodrás ver estadísticas detalladas del desempeño de los estudiantes y las preguntas.\nAdemás, puedes descargar el reporte en formato Excel(1), exportar el reporte a onredrive(2) o a drive(3).",
            "imagenes": [
                "https://drive.google.com/thumbnail?id=1c9kgA68uxUGNSwFp-U2CTi96t6JrzeTO&sz=w1600",
                "https://drive.google.com/thumbnail?id=1vfy0wGLRCF236dST6RP_hKCUcgjzWQ6n&sz=w1600",
            ],
        },
    ]

    faqs = [
        {"q": "¿Qué hago si el PIN dice inválido?", "a": "Reinicia la partida y verifica que compartiste el PIN correcto."},
        {"q": "¿Cuántos alumnos pueden unirse?", "a": "Depende de tu plan; en general con 30-100 concurrentes funcionan bien."},
        {"q": "¿Un alumno perdió su conexión antes de que el profesor iniciara la partida?", "a": "Puede reingresar con el mismo PIN y su nombre de usuario."},
    ]
    return render_template("guia.html", pasos=pasos, faqs=faqs)
