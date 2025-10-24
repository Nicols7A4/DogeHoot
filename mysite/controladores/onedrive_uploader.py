"""
MÓDULO DE SUBIDA A ONEDRIVE - DogeHoot
=======================================
Este módulo maneja la subida de archivos a OneDrive
usando la API de Microsoft Graph

Autor: DogeHoot Team
Fecha: 23 de octubre de 2025
"""

import os
import requests
from datetime import datetime, timedelta

# Configuración de OneDrive/Microsoft Graph
CLIENT_ID = os.getenv('ONEDRIVE_CLIENT_ID')
CLIENT_SECRET = os.getenv('ONEDRIVE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('ONEDRIVE_REDIRECT_URI', 'http://localhost:5001/onedrive/callback')

# Ruta del archivo de tokens - buscar en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_FILE = os.path.join(BASE_DIR, 'token_onedrive.json')


class OneDriveUploader:
    """Clase para subir archivos a OneDrive"""
    
    def __init__(self, token_file=TOKEN_FILE):
        """
        Inicializa el uploader de OneDrive
        
        Args:
            token_file (str): Ruta al archivo token_onedrive.json
        """
        self.token_file = token_file
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()
    
    def _load_tokens(self):
        """Carga los tokens desde el archivo JSON"""
        import json
        
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
                print(f"Error al cargar tokens: {e}")
    
    def _save_tokens(self, access_token, refresh_token=None, expires_in=3600):
        """Guarda los tokens en el archivo JSON"""
        import json
        
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
            raise Exception("No hay refresh token disponible. Necesitas autenticarte primero.")
        
        url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
        
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
        else:
            raise Exception(f"Error al refrescar token: {response.text}")
    
    def get_authorization_url(self):
        """
        Genera la URL de autorización para que el usuario inicie sesión
        
        Returns:
            str: URL de autorización
        """
        from urllib.parse import urlencode
        
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': 'Files.ReadWrite.All offline_access',
            'response_mode': 'query'
        }
        
        auth_url = f'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?{urlencode(params)}'
        
        print("="*60)
        print(f"🔗 URL de autorización generada:")
        print(f"   {auth_url}")
        print(f"📍 Redirect URI configurado: {REDIRECT_URI}")
        print(f"🆔 Client ID: {CLIENT_ID}")
        print("="*60)
        
        return auth_url
    
    def exchange_code_for_tokens(self, code):
        """
        Intercambia el código de autorización por tokens de acceso
        
        Args:
            code (str): Código de autorización recibido del redirect
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
        
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'scope': 'Files.ReadWrite.All offline_access'
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self._save_tokens(
                token_data['access_token'],
                token_data.get('refresh_token'),
                token_data.get('expires_in', 3600)
            )
            return {
                'success': True,
                'message': 'Autenticación exitosa'
            }
        else:
            return {
                'success': False,
                'message': f'Error en autenticación: {response.text}'
            }
    
    def subir_archivo(self, ruta_archivo, nombre_drive=None, folder_path='DogeHoot'):
        """
        Sube un archivo a OneDrive
        
        Args:
            ruta_archivo (str): Ruta local del archivo a subir
            nombre_drive (str, optional): Nombre del archivo en OneDrive
            folder_path (str): Ruta de la carpeta en OneDrive (default: 'DogeHoot')
            
        Returns:
            dict: {'success': bool, 'message': str, 'file_id': str, 'web_url': str}
        """
        if not os.path.exists(ruta_archivo):
            return {
                'success': False,
                'message': f'El archivo {ruta_archivo} no existe'
            }
        
        if not self.access_token:
            return {
                'success': False,
                'message': 'No hay token de acceso. Necesitas autenticarte primero.'
            }
        
        # Usar nombre original si no se especifica
        if nombre_drive is None:
            nombre_drive = os.path.basename(ruta_archivo)
        
        # Construir la ruta del archivo en OneDrive
        upload_path = f"/{folder_path}/{nombre_drive}" if folder_path else f"/{nombre_drive}"
        
        try:
            # Leer el archivo
            with open(ruta_archivo, 'rb') as f:
                file_content = f.read()
            
            # URL de la API para subir archivo
            url = f'https://graph.microsoft.com/v1.0/me/drive/root:{upload_path}:/content'
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(url, headers=headers, data=file_content)
            
            if response.status_code in [200, 201]:
                file_data = response.json()
                return {
                    'success': True,
                    'message': f'Archivo subido exitosamente: {nombre_drive}',
                    'file_id': file_data.get('id'),
                    'file_name': file_data.get('name'),
                    'web_url': file_data.get('webUrl'),
                    'download_url': file_data.get('@microsoft.graph.downloadUrl')
                }
            elif response.status_code == 401:
                # Token expirado, intentar refrescar
                self._refresh_access_token()
                # Reintentar la subida
                return self.subir_archivo(ruta_archivo, nombre_drive, folder_path)
            else:
                return {
                    'success': False,
                    'message': f'Error al subir archivo: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al subir archivo: {str(e)}'
            }
    
    def subir_desde_memoria(self, contenido, nombre_archivo, folder_path='DogeHoot'):
        """
        Sube un archivo desde memoria (bytes) a OneDrive
        
        Args:
            contenido (bytes): Contenido del archivo en bytes
            nombre_archivo (str): Nombre del archivo en OneDrive
            folder_path (str): Ruta de la carpeta en OneDrive
            
        Returns:
            dict: Resultado de la subida
        """
        if not self.access_token:
            return {
                'success': False,
                'message': 'No hay token de acceso. Necesitas autenticarte primero.'
            }
        
        # Construir la ruta del archivo en OneDrive
        upload_path = f"/{folder_path}/{nombre_archivo}" if folder_path else f"/{nombre_archivo}"
        
        try:
            url = f'https://graph.microsoft.com/v1.0/me/drive/root:{upload_path}:/content'
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(url, headers=headers, data=contenido)
            
            if response.status_code in [200, 201]:
                file_data = response.json()
                return {
                    'success': True,
                    'message': f'Archivo subido exitosamente desde memoria: {nombre_archivo}',
                    'file_id': file_data.get('id'),
                    'file_name': file_data.get('name'),
                    'web_url': file_data.get('webUrl'),
                    'download_url': file_data.get('@microsoft.graph.downloadUrl')
                }
            elif response.status_code == 401:
                # Token expirado, intentar refrescar
                self._refresh_access_token()
                # Reintentar la subida
                return self.subir_desde_memoria(contenido, nombre_archivo, folder_path)
            else:
                return {
                    'success': False,
                    'message': f'Error al subir archivo: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al subir archivo desde memoria: {str(e)}'
            }
    
    def crear_carpeta(self, nombre_carpeta, parent_path=''):
        """
        Crea una carpeta en OneDrive
        
        Args:
            nombre_carpeta (str): Nombre de la carpeta
            parent_path (str): Ruta de la carpeta padre (vacío = raíz)
            
        Returns:
            dict: {'success': bool, 'message': str, 'folder_id': str}
        """
        if not self.access_token:
            return {
                'success': False,
                'message': 'No hay token de acceso.'
            }
        
        try:
            if parent_path:
                url = f'https://graph.microsoft.com/v1.0/me/drive/root:/{parent_path}:/children'
            else:
                url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'name': nombre_carpeta,
                'folder': {},
                '@microsoft.graph.conflictBehavior': 'rename'
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                folder_data = response.json()
                return {
                    'success': True,
                    'message': f'Carpeta creada: {nombre_carpeta}',
                    'folder_id': folder_data.get('id'),
                    'folder_name': folder_data.get('name'),
                    'web_url': folder_data.get('webUrl')
                }
            else:
                return {
                    'success': False,
                    'message': f'Error al crear carpeta: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al crear carpeta: {str(e)}'
            }


# Funciones auxiliares para uso rápido
def subir_archivo_rapido(ruta_archivo, nombre_drive=None, folder_path='DogeHoot'):
    """
    Función auxiliar para subir archivos rápidamente
    
    Args:
        ruta_archivo (str): Ruta del archivo a subir
        nombre_drive (str, optional): Nombre en OneDrive
        folder_path (str): Carpeta destino en OneDrive
        
    Returns:
        dict: Resultado de la subida
    """
    uploader = OneDriveUploader()
    return uploader.subir_archivo(ruta_archivo, nombre_drive, folder_path)


def subir_excel_a_onedrive(ruta_excel, nombre_drive=None, folder_path='DogeHoot Reportes'):
    """
    Función específica para subir archivos Excel a OneDrive
    
    Args:
        ruta_excel (str): Ruta del archivo Excel
        nombre_drive (str, optional): Nombre en OneDrive
        folder_path (str): Carpeta destino
        
    Returns:
        dict: Resultado de la subida
    """
    uploader = OneDriveUploader()
    return uploader.subir_archivo(ruta_excel, nombre_drive, folder_path)
