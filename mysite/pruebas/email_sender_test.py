"""
MÓDULO DE ENVÍO DE CORREOS - DogeHoot
======================================
Este módulo maneja el envío de correos electrónicos con archivos adjuntos
para Gmail y Hotmail (aunque Hotmail tiene limitaciones en PythonAnywhere)

Autor: DogeHoot Team
Fecha: 23 de octubre de 2025
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()


class EmailSender:
    """Clase para enviar correos electrónicos con archivos adjuntos"""
    
    def __init__(self):
        """Inicializa las configuraciones de Gmail y Hotmail"""
        # Configuración Gmail
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        self.gmail_smtp = os.getenv('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.gmail_port = int(os.getenv('GMAIL_SMTP_PORT', 587))
        
        # Configuración Hotmail
        self.hotmail_user = os.getenv('HOTMAIL_USER')
        self.hotmail_password = os.getenv('HOTMAIL_APP_PASSWORD')
        self.hotmail_smtp = os.getenv('OUTLOOK_SMTP_SERVER', 'smtp-mail.outlook.com')
        self.hotmail_port = int(os.getenv('OUTLOOK_SMTP_PORT', 587))
    
    def enviar_correo_gmail(self, destinatario, asunto, mensaje_html, archivo_adjunto=None):
        """
        Envía un correo usando Gmail
        
        Args:
            destinatario (str): Correo del destinatario
            asunto (str): Asunto del correo
            mensaje_html (str): Contenido HTML del mensaje
            archivo_adjunto (str, optional): Ruta del archivo a adjuntar
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        if not self.gmail_user or not self.gmail_password:
            return {
                'success': False, 
                'message': 'Credenciales de Gmail no configuradas en .env'
            }
        
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # Agregar cuerpo del mensaje
            msg.attach(MIMEText(mensaje_html, 'html'))
            
            # Adjuntar archivo si existe
            if archivo_adjunto and os.path.exists(archivo_adjunto):
                self._adjuntar_archivo(msg, archivo_adjunto)
            
            # Conectar y enviar
            server = smtplib.SMTP(self.gmail_smtp, self.gmail_port)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            return {
                'success': True, 
                'message': f'Correo enviado exitosamente a {destinatario} desde Gmail'
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False, 
                'message': 'Error de autenticación. Verifica tu contraseña de aplicación de Gmail'
            }
        except Exception as e:
            return {
                'success': False, 
                'message': f'Error al enviar correo por Gmail: {str(e)}'
            }
    
    def enviar_correo_hotmail(self, destinatario, asunto, mensaje_html, archivo_adjunto=None):
        """
        Envía un correo usando Hotmail/Outlook
        
        ⚠️ ADVERTENCIA: En PythonAnywhere gratuito, Outlook SMTP está bloqueado
        
        Args:
            destinatario (str): Correo del destinatario
            asunto (str): Asunto del correo
            mensaje_html (str): Contenido HTML del mensaje
            archivo_adjunto (str, optional): Ruta del archivo a adjuntar
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        if not self.hotmail_user or not self.hotmail_password:
            return {
                'success': False, 
                'message': 'Credenciales de Hotmail no configuradas en .env'
            }
        
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.hotmail_user
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # Agregar cuerpo del mensaje
            msg.attach(MIMEText(mensaje_html, 'html'))
            
            # Adjuntar archivo si existe
            if archivo_adjunto and os.path.exists(archivo_adjunto):
                self._adjuntar_archivo(msg, archivo_adjunto)
            
            # Conectar y enviar
            server = smtplib.SMTP(self.hotmail_smtp, self.hotmail_port)
            server.starttls()
            server.login(self.hotmail_user, self.hotmail_password)
            server.send_message(msg)
            server.quit()
            
            return {
                'success': True, 
                'message': f'Correo enviado exitosamente a {destinatario} desde Hotmail'
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False, 
                'message': 'Error de autenticación. Verifica tu contraseña de aplicación de Hotmail'
            }
        except smtplib.SMTPConnectError:
            return {
                'success': False, 
                'message': '⚠️ No se pudo conectar. En PythonAnywhere gratuito, Outlook SMTP está bloqueado'
            }
        except Exception as e:
            return {
                'success': False, 
                'message': f'Error al enviar correo por Hotmail: {str(e)}'
            }
    
    def _adjuntar_archivo(self, msg, ruta_archivo):
        """
        Adjunta un archivo al mensaje
        
        Args:
            msg (MIMEMultipart): Mensaje al que adjuntar
            ruta_archivo (str): Ruta del archivo a adjuntar
        """
        nombre_archivo = os.path.basename(ruta_archivo)
        
        with open(ruta_archivo, 'rb') as archivo:
            parte = MIMEBase('application', 'octet-stream')
            parte.set_payload(archivo.read())
        
        encoders.encode_base64(parte)
        parte.add_header(
            'Content-Disposition',
            f'attachment; filename= {nombre_archivo}'
        )
        
        msg.attach(parte)
    
    def enviar_reporte_excel(self, destinatario, tipo_servicio, archivo_excel):
        """
        Envía un reporte de Excel según el tipo de servicio (Drive o OneDrive)
        
        Args:
            destinatario (str): Correo del destinatario
            tipo_servicio (str): 'drive' o 'onedrive'
            archivo_excel (str): Ruta del archivo Excel a enviar
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        if not os.path.exists(archivo_excel):
            return {
                'success': False, 
                'message': f'El archivo {archivo_excel} no existe'
            }
        
        # Determinar el servicio según el tipo
        tipo_servicio = tipo_servicio.lower()
        
        # Plantilla HTML del mensaje
        mensaje_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #4A90E2; text-align: center;">🎮 DogeHoot - Reporte de Partidas</h2>
                    <hr style="border: 1px solid #eee;">
                    <p>¡Hola!</p>
                    <p>Te enviamos el reporte de tus partidas en formato Excel adjunto a este correo.</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>📊 Archivo:</strong> {os.path.basename(archivo_excel)}</p>
                        <p style="margin: 5px 0;"><strong>📅 Fecha:</strong> {self._obtener_fecha_actual()}</p>
                        <p style="margin: 5px 0;"><strong>☁️ Servicio:</strong> {'Google Drive' if tipo_servicio == 'drive' else 'OneDrive'}</p>
                    </div>
                    <p>Gracias por usar DogeHoot 🐕</p>
                    <hr style="border: 1px solid #eee;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        Este correo fue generado automáticamente. Por favor no respondas a este mensaje.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Enviar según el tipo de servicio
        if tipo_servicio == 'drive':
            # Enviar por Gmail para Google Drive
            return self.enviar_correo_gmail(
                destinatario=destinatario,
                asunto='📊 DogeHoot - Reporte de Partidas (Google Drive)',
                mensaje_html=mensaje_html,
                archivo_adjunto=archivo_excel
            )
        elif tipo_servicio == 'onedrive':
            # Enviar por Hotmail para OneDrive
            return self.enviar_correo_hotmail(
                destinatario=destinatario,
                asunto='📊 DogeHoot - Reporte de Partidas (OneDrive)',
                mensaje_html=mensaje_html,
                archivo_adjunto=archivo_excel
            )
        else:
            return {
                'success': False, 
                'message': f'Tipo de servicio inválido: {tipo_servicio}. Use "drive" o "onedrive"'
            }
    
    def _obtener_fecha_actual(self):
        """Obtiene la fecha actual formateada"""
        from datetime import datetime
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


# Función auxiliar para uso rápido
def enviar_reporte_rapido(destinatario, tipo_servicio, archivo_excel):
    """
    Función auxiliar para enviar reportes rápidamente
    
    Args:
        destinatario (str): Correo del destinatario
        tipo_servicio (str): 'drive' o 'onedrive'
        archivo_excel (str): Ruta del archivo Excel
        
    Returns:
        dict: Resultado del envío
    """
    sender = EmailSender()
    return sender.enviar_reporte_excel(destinatario, tipo_servicio, archivo_excel)
