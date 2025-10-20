# controladores/email_sender.py

import os
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- Ruta absoluta al token.json (sin cambios) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, '..', 'token.json')

# --- 1. Plantilla Base del Correo (tu idea, ¡perfecta!) ---
def _html_base():
    """Devuelve el encabezado y los estilos del correo."""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>DogeHoot!</title>
        <style>
            body {
                    font-family: 'Poppins', Arial, sans-serif;
                background-color: #FFF9ED; /* --main-bg */
                padding: 20px;
                margin: 0;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            .container {
                max-width: 600px;
                margin: 40px auto;
                background: #FFFFFF; /* --panel-bg */
                border-radius: 24px;
                border: 1px solid #E0E0E0; /* --border-soft */
                box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
                padding: 40px;
                text-align: center;
            }
            .logo {
                max-width: 180px;
                margin-bottom: 30px;
            }
            h2 {
                font-size: 1.8rem;
                font-weight: 700;
                color: #333333; /* --text-color */
                margin: 0 0 15px;
            }
            p {
                color: #333333; /* --text-color */
                line-height: 1.6;
                font-size: 16px;
                margin: 0 0 30px;
            }
            .code {
                font-size: 2.5rem;
                font-weight: 700;
                letter-spacing: 0.5rem;
                color: #1E88E5; /* --btn-inprogress-text */
                margin: 20px 0;
                padding: 15px 25px;
                background-color: #E6F2FF; /* --btn-inprogress-bg */
                border-radius: 12px;
                display: inline-block;
            }
            hr {
                border: none;
                border-top: 1px solid #E0E0E0; /* --border-soft */
                margin: 30px auto;
                width: 80%;
            }
            .footer-text {
                font-size: 14px;
                color: #6c757d; /* --text-muted */
                margin-top: 30px;
                margin-bottom: 0;
            }
            .btn-verificar {
                display: inline-block;
                padding: 15px 30px;
                margin-top: 20px;
                background-color: #2BB673;
                color: white !important; /* !important para asegurar que se vea en Gmail */
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                font-size: 16px;
            }

            .btn-email{
  display:inline-block;
  padding:16px 36px;
  border-radius:14px;
  background:#F05A2A;         /* naranja DogeHoot */
  color:#ffffff !important;    /* texto blanco en Gmail/Outlook */
  text-decoration:none !important;
  font-weight:700;
  font-size:18px;
  line-height:1.2;
  letter-spacing:.2px;
  box-shadow:0 6px 0 #D74E21, 0 10px 18px rgba(240,90,42,.22);
}

/* Específico para el de restablecer (alias de seguridad) */
.btn-email.btn-restablecer{
  background:#F05A2A !important;
  box-shadow:0 6px 0 #D74E21, 0 10px 18px rgba(240,90,42,.22) !important;
}

/* Pequeña interacción (no todos los clientes soportan :hover) */
.btn-email:hover{
  filter:brightness(1.05);
}

/* “Click” visual (algunos clientes sí lo aplican) */
.btn-email:active{
  transform:translateY(1px);
  box-shadow:0 5px 0 #D74E21, 0 8px 14px rgba(240,90,42,.2);
}

/* En móviles, que no se vea minúsculo */
@media only screen and (max-width:480px){
  .btn-email{ width:100%; box-sizing:border-box; }
}
        </style>
    </head>
    """

# --- 2. Función Genérica para Enviar CUALQUIER Correo ---
def _enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Función interna que se encarga de la lógica de envío con la API de Gmail.
    """
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)

        # Construye el contenido completo del correo
        html_completo = _html_base() + cuerpo_html

        message = MIMEText(html_completo, 'html')
        message['To'] = destinatario
        message['From'] = 'dogehootnotifications@gmail.com'
        message['Subject'] = asunto

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        service.users().messages().send(userId="me", body=create_message).execute()

        print(f"Correo enviado a {destinatario} con asunto: {asunto}")
        return True, "Correo enviado"
    except Exception as e:
        print(f"Ocurrió un error al enviar el correo: {e}")
        return False, str(e)

# --- 3. Funciones Públicas (las que llaman tus rutas) ---

def enviar_correo_verificacion(destinatario, codigo):
    """Prepara y envía el correo de bienvenida y verificación."""
    asunto = "Tu Código de Verificación - DogeHoot!"
    cuerpo = f"""
    <body>
        <div class="container">
            <h2>¡Ya casi estás!</h2>
            <p>Gracias por registrarte. Usa el siguiente código para verificar tu cuenta:</p>
            <div class="code">{codigo}</div>
            <a href="https://dmailproject.pythonanywhere.com/verificar?email={destinatario}&codigo={codigo}" class="btn-verificar">O haz clic aquí para verificar</a>
            <hr>
            <p class="footer-text">Si no te registraste, ignora este correo.</p>
        </div>
    </body>
    </html>
    """
    # Llama a la función genérica para hacer el envío
    return _enviar_correo(destinatario, asunto, cuerpo)

def enviar_correo_codigo_nuevo(destinatario, codigo):
    """Prepara y envía el correo para un código reenviado."""
    asunto = "Tu Nuevo Código de Verificación - DogeHoot!"
    cuerpo = f"""
    <body>
        <div class="container">
            <h2>Aquí tienes tu nuevo código</h2>
            <p>Usa el siguiente código para verificar tu cuenta:</p>
            <div class="code">{codigo}</div>
            <a href="https://dmailproject.pythonanywhere.com/verificar?email={destinatario}&codigo={codigo}" class="btn-verificar">O haz clic aquí para verificar</a>
            <hr>
            <p class="footer-text">Si no solicitaste un nuevo código, podés ignorar este correo.</p>
        </div>
    </body>
    </html>
    """
    return _enviar_correo(destinatario, asunto, cuerpo)

def enviar_correo_restablecimiento(destinatario, url_restablecimiento):
    """Prepara y envía el correo con el enlace de restablecimiento."""
    asunto = "Restablece tu contraseña de DogeHoot!"
    cuerpo = f"""
    <body>
        <div class="container">
            <h2>¿Olvidaste tu contraseña?</h2>
            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta. Haz clic en el botón de abajo para elegir una nueva. Este enlace es válido por 15 minutos.</p>
            <a href="{url_restablecimiento}" class="btn-email btn-restablecer">Restablecer Contraseña</a>
            <hr>
            <p class="footer-text">Si no solicitaste esto, puedes ignorar este correo de forma segura.</p>
        </div>
    </body>
    </html>
    """
    # Llama a la función genérica que ya tienes para hacer el envío
    return _enviar_correo(destinatario, asunto, cuerpo)
# --- FIN: FUNCIÓN AÑADIDA ---