"""
MÓDULO DE ENVÍO DE CORREOS VÍA MICROSOFT GRAPH API - DogeHoot
==============================================================
Este módulo maneja el envío de correos electrónicos usando Microsoft Graph API
Compatible con PythonAnywhere free tier (usa HTTPS en lugar de SMTP)

Autor: DogeHoot Team
Fecha: 27 de octubre de 2025
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Microsoft Graph
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('AZURE_REDIRECT_URI', 'http://localhost:5001/onedrive/callback')

# Ruta del archivo de tokens - mismo archivo que OneDrive
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_FILE = os.path.join(BASE_DIR, 'token_onedrive.json')


class OutlookEmailSender:
    """Clase para enviar correos electrónicos usando Microsoft Graph API"""
    
    def __init__(self, token_file=TOKEN_FILE):
        """
        Inicializa el sender de Outlook
        
        Args:
            token_file (str): Ruta al archivo token_onedrive.json
        """
        self.token_file = token_file
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()
    
    def _load_tokens(self):
        """Carga los tokens desde el archivo JSON"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    
                    # Verificar si el token ha expirado
                    expires_at = data.get('expires_at')
                    if expires_at:
                        if datetime.now().timestamp() >= expires_at:
                            # Token expirado, intentar refrescar
                            self._refresh_access_token()
            except Exception as e:
                print(f"⚠️  Error al cargar tokens: {e}")
    
    def _save_tokens(self, access_token, refresh_token=None, expires_in=3600):
        """Guarda los tokens en el archivo JSON"""
        data = {
            'access_token': access_token,
            'refresh_token': refresh_token or self.refresh_token,
            'expires_at': (datetime.now() + timedelta(seconds=expires_in)).timestamp()
        }
        
        with open(self.token_file, 'w') as f:
            json.dump(data, f)
        
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
    
    def _refresh_access_token(self):
        """Refresca el access token usando el refresh token"""
        if not self.refresh_token:
            raise Exception("No hay refresh token disponible. Necesitas autenticarte primero con Mail.Send permisos.")
        
        url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
            'redirect_uri': REDIRECT_URI
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self._save_tokens(
                token_data['access_token'],
                token_data.get('refresh_token'),
                token_data.get('expires_in', 3600)
            )
            print("✅ Token refrescado exitosamente")
        else:
            raise Exception(f"Error al refrescar token: {response.text}")
    
    # --- Plantilla Base del Correo ---
    def _html_base(self):
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
                    color: white !important;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                }
                .btn-email {
                    display: inline-block;
                    padding: 16px 36px;
                    border-radius: 14px;
                    background: #F05A2A;
                    color: #ffffff !important;
                    text-decoration: none !important;
                    font-weight: 700;
                    font-size: 18px;
                    line-height: 1.2;
                    letter-spacing: .2px;
                    box-shadow: 0 6px 0 #D74E21, 0 10px 18px rgba(240,90,42,.22);
                }
                .btn-email.btn-restablecer {
                    background: #F05A2A !important;
                    box-shadow: 0 6px 0 #D74E21, 0 10px 18px rgba(240,90,42,.22) !important;
                }
                .btn-email:hover {
                    filter: brightness(1.05);
                }
                .btn-email:active {
                    transform: translateY(1px);
                    box-shadow: 0 5px 0 #D74E21, 0 8px 14px rgba(240,90,42,.2);
                }
                @media only screen and (max-width:480px) {
                    .btn-email { width: 100%; box-sizing: border-box; }
                }
            </style>
        </head>
        """
    
    def enviar_correo(self, destinatario, asunto, cuerpo_html, max_retries=2):
        """
        Envía un correo usando Microsoft Graph API
        
        Args:
            destinatario (str): Correo del destinatario
            asunto (str): Asunto del correo
            cuerpo_html (str): Cuerpo HTML del correo
            max_retries (int): Número de reintentos en caso de error 401
            
        Returns:
            tuple: (bool, str) - (éxito, mensaje)
        """
        if not self.access_token:
            return False, "No hay token de acceso. Necesitas autenticarte primero con permisos Mail.Send."
        
        # Construir el HTML completo
        html_completo = self._html_base() + cuerpo_html
        
        # Endpoint de Microsoft Graph para enviar correo
        url = 'https://graph.microsoft.com/v1.0/me/sendMail'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Estructura del mensaje según Microsoft Graph API
        message = {
            'message': {
                'subject': asunto,
                'body': {
                    'contentType': 'HTML',
                    'content': html_completo
                },
                'toRecipients': [
                    {
                        'emailAddress': {
                            'address': destinatario
                        }
                    }
                ]
            },
            'saveToSentItems': 'true'
        }
        
        for intento in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=message)
                
                if response.status_code == 202:
                    # 202 Accepted = correo enviado exitosamente
                    print(f"✅ Correo enviado a {destinatario} con asunto: {asunto}")
                    return True, "Correo enviado exitosamente"
                    
                elif response.status_code == 401:
                    # Token expirado, intentar refrescar
                    if intento < max_retries - 1:
                        print(f"⚠️  Token expirado (401). Refrescando... (intento {intento + 1}/{max_retries})")
                        self._refresh_access_token()
                        continue
                    else:
                        return False, "Error de autenticación. Por favor, vuelve a autenticarte con permisos Mail.Send."
                        
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    print(f"❌ Error al enviar correo: {error_msg}")
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"Excepción al enviar correo: {str(e)}"
                print(f"❌ {error_msg}")
                if intento < max_retries - 1:
                    continue
                return False, error_msg
        
        return False, "No se pudo enviar el correo después de varios intentos."
    
    # --- Funciones Públicas para Tipos de Correos Específicos ---
    
    def enviar_correo_verificacion(self, destinatario, codigo):
        """
        Prepara y envía el correo de bienvenida y verificación
        
        Args:
            destinatario (str): Correo del destinatario
            codigo (str): Código de verificación
            
        Returns:
            tuple: (bool, str) - (éxito, mensaje)
        """
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
        return self.enviar_correo(destinatario, asunto, cuerpo)
    
    def enviar_correo_codigo_nuevo(self, destinatario, codigo):
        """
        Prepara y envía el correo para un código reenviado
        
        Args:
            destinatario (str): Correo del destinatario
            codigo (str): Nuevo código de verificación
            
        Returns:
            tuple: (bool, str) - (éxito, mensaje)
        """
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
        return self.enviar_correo(destinatario, asunto, cuerpo)
    
    def enviar_correo_restablecimiento(self, destinatario, url_restablecimiento):
        """
        Prepara y envía el correo con el enlace de restablecimiento
        
        Args:
            destinatario (str): Correo del destinatario
            url_restablecimiento (str): URL para restablecer contraseña
            
        Returns:
            tuple: (bool, str) - (éxito, mensaje)
        """
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
        return self.enviar_correo(destinatario, asunto, cuerpo)
    
    def enviar_correo_con_link_onedrive(self, email_destinatario, nombre_archivo, link_onedrive):
        """
        Prepara y envía el correo con el enlace de descarga de OneDrive
        
        Args:
            email_destinatario (str): Correo del destinatario
            nombre_archivo (str): Nombre del archivo compartido
            link_onedrive (str): URL del archivo en OneDrive
            
        Returns:
            dict: {'success': bool, 'message': str, 'email_sent_to': str}
        """
        print(f"📧 Intentando enviar correo a: {email_destinatario}")
        print(f"📄 Archivo: {nombre_archivo}")
        print(f"🔗 Link: {link_onedrive}")
        
        asunto = f"📊 Reporte DogeHoot - {nombre_archivo}"
        cuerpo = f"""
        <body>
            <div class="container">
                <h2>🐕 Tu Reporte está Listo!</h2>
                <p>Hola! Tu reporte de DogeHoot ha sido generado exitosamente y está disponible para descargar.</p>
                <p><strong>Archivo:</strong> {nombre_archivo}</p>
                <a href="{link_onedrive}" class="btn-email" target="_blank">📥 Descargar Reporte</a>
                <hr>
                <p class="footer-text">Este enlace te permite ver y descargar el archivo desde OneDrive.</p>
                <p class="footer-text">Si no solicitaste este reporte, puedes ignorar este correo.</p>
            </div>
        </body>
        </html>
        """
        
        try:
            success, message = self.enviar_correo(email_destinatario, asunto, cuerpo)
            
            if success:
                print(f"✅ Correo enviado exitosamente a {email_destinatario}")
            else:
                print(f"❌ Error al enviar correo: {message}")
            
            return {
                'success': success,
                'message': message,
                'email_sent_to': email_destinatario
            }
        except Exception as e:
            print(f"❌ Excepción al enviar correo: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error al enviar correo: {str(e)}',
                'email_sent_to': email_destinatario
            }


# --- Funciones Auxiliares para Compatibilidad ---

def _enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Función auxiliar para compatibilidad con código existente
    Reemplaza la función del módulo email_sender.py
    """
    sender = OutlookEmailSender()
    return sender.enviar_correo(destinatario, asunto, cuerpo_html)


def enviar_correo_verificacion(destinatario, codigo):
    """Función auxiliar para enviar correo de verificación"""
    sender = OutlookEmailSender()
    return sender.enviar_correo_verificacion(destinatario, codigo)


def enviar_correo_codigo_nuevo(destinatario, codigo):
    """Función auxiliar para enviar nuevo código de verificación"""
    sender = OutlookEmailSender()
    return sender.enviar_correo_codigo_nuevo(destinatario, codigo)


def enviar_correo_restablecimiento(destinatario, url_restablecimiento):
    """Función auxiliar para enviar correo de restablecimiento de contraseña"""
    sender = OutlookEmailSender()
    return sender.enviar_correo_restablecimiento(destinatario, url_restablecimiento)


def enviar_correo_con_link_onedrive(email_destinatario, nombre_archivo, link_onedrive):
    """Función auxiliar para enviar correo con link de OneDrive"""
    sender = OutlookEmailSender()
    return sender.enviar_correo_con_link_onedrive(email_destinatario, nombre_archivo, link_onedrive)
