import sys
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_mail import Mail, Message
from controladores.importarExcel import importar_bp # TEST EXCEL aún

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
# Cargar el .env desde la raíz del proyecto (un nivel arriba de mysite)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

sys.modules.setdefault('main', sys.modules.get('__main__'))

from controladores.controlador_recompensas import otorgar_recompensas
from controladores.foto_perfil import perfil_bp

from flask_jwt import JWT, jwt_required
from User_auth import authenticate, identity

app = Flask(__name__)

# ⚠️ IMPORTANTE: Configurar SECRET_KEY ANTES de inicializar JWT
app.config['SECRET_KEY'] = 'Tralalero Tralala'

# Configurar JWT para usar 'correo' en lugar de 'username'
# app.config['JWT_AUTH_USERNAME_KEY'] = 'correo'

jwt = JWT(app, authenticate, identity)

# Registrar blueprint de perfil (controlador independiente)
app.register_blueprint(perfil_bp) #agregado por pame. NOTA: Se puede borrar

# TEST EXCEL, Línea de prueba para el Importar Cuestionario
app.register_blueprint(importar_bp)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dogehootnotifications@gmail.com'
app.config['MAIL_PASSWORD'] = 'Dmail123.'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

import routes_web
import routes_api

#Para que el usuario suba una foto para su perfil
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
app.config['AVATAR_ALLOWED'] = {'png', 'jpg', 'jpeg', 'webp'}

app.config['AVATAR_UPLOAD_FOLDER'] = os.path.join(
    app.root_path, 'static', 'img', 'usuario'
)

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['AVATAR_ALLOWED']

def _unique_name(user_id, ext):
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"user_{user_id}_{ts}.{ext}"


# Iniciar el servidor
if __name__ == "__main__":
    # Ejecutar sin Socket.IO (solo HTTP)
    app.run(debug=True, port=5001)
    

    #---------------------------prueba recompensa

@app.route("/test_recompensas/<int:id_partida>")
def test_recompensas(id_partida):
    otorgar_recompensas(id_partida)
    return f"Recompensas otorgadas para la partida {id_partida}"


# Go