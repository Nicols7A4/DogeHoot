"""
MÓDULO DE SUBIDA A GOOGLE DRIVE - DogeHoot
===========================================
Este módulo maneja la subida de archivos a Google Drive
usando la API de Google Drive v3

Autor: DogeHoot Team
Fecha: 23 de octubre de 2025
"""

import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import pickle

# Scopes necesarios para Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Crear y editar archivos
    'https://www.googleapis.com/auth/drive.appdata'  # Datos de la app
]


class GoogleDriveUploader:
    """Clase para subir archivos a Google Drive"""
    
    def __init__(self, credentials_file='credentials.json', token_file='token_drive.json'):
        """
        Inicializa el uploader de Google Drive
        
        IMPORTANTE PARA PYTHONANYWHERE:
        - Ejecuta este script EN TU PC LOCAL primero para generar token_drive.json
        - Luego sube credentials.json y token_drive.json a PythonAnywhere
        - Usa rutas ABSOLUTAS en PythonAnywhere, ejemplo:
          '/home/usuario/DogeHoot-2/mysite/credentials.json'
        
        Args:
            credentials_file (str): Ruta al archivo credentials.json
            token_file (str): Ruta al archivo token_drive.json
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Drive API"""
        creds = None
        
        # Verificar si existe token guardado
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Error al cargar token: {e}")
                creds = None
        
        # Si no hay credenciales válidas, obtener nuevas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error al refrescar token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"No se encontró {self.credentials_file}. "
                        "Descárgalo desde Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Guardar credenciales para la próxima vez
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Crear servicio de Drive
        self.service = build('drive', 'v3', credentials=creds)
    
    def subir_archivo(self, ruta_archivo, nombre_drive=None, folder_id=None, mime_type=None):
        """
        Sube un archivo a Google Drive
        
        Args:
            ruta_archivo (str): Ruta local del archivo a subir
            nombre_drive (str, optional): Nombre del archivo en Drive (por defecto usa el nombre local)
            folder_id (str, optional): ID de la carpeta en Drive donde subir (None = raíz)
            mime_type (str, optional): Tipo MIME del archivo (se detecta automáticamente si no se proporciona)
            
        Returns:
            dict: {'success': bool, 'message': str, 'file_id': str, 'web_view_link': str}
        """
        if not os.path.exists(ruta_archivo):
            return {
                'success': False,
                'message': f'El archivo {ruta_archivo} no existe'
            }
        
        try:
            # Usar nombre original si no se especifica
            if nombre_drive is None:
                nombre_drive = os.path.basename(ruta_archivo)
            
            # Metadatos del archivo
            file_metadata = {'name': nombre_drive}
            
            # Si se especifica carpeta, agregar a metadatos
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Detectar tipo MIME si no se proporciona
            if mime_type is None:
                mime_type = self._detectar_mime_type(ruta_archivo)
            
            # Subir archivo
            media = MediaFileUpload(ruta_archivo, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            return {
                'success': True,
                'message': f'Archivo subido exitosamente: {nombre_drive}',
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
            
        except HttpError as error:
            return {
                'success': False,
                'message': f'Error HTTP al subir archivo: {error}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al subir archivo: {str(e)}'
            }
    
    def subir_desde_memoria(self, contenido, nombre_archivo, mime_type='text/plain', folder_id=None):
        """
        Sube un archivo desde memoria (sin guardarlo en disco)
        
        Args:
            contenido (bytes): Contenido del archivo en bytes
            nombre_archivo (str): Nombre del archivo en Drive
            mime_type (str): Tipo MIME del archivo
            folder_id (str, optional): ID de la carpeta en Drive
            
        Returns:
            dict: Resultado de la subida
        """
        try:
            # Metadatos del archivo
            file_metadata = {'name': nombre_archivo}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Crear media desde bytes
            fh = io.BytesIO(contenido)
            media = MediaIoBaseUpload(fh, mimetype=mime_type, resumable=True)
            
            # Subir archivo
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            return {
                'success': True,
                'message': f'Archivo subido exitosamente desde memoria: {nombre_archivo}',
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al subir archivo desde memoria: {str(e)}'
            }
    
    def crear_carpeta(self, nombre_carpeta, parent_folder_id=None):
        """
        Crea una carpeta en Google Drive
        
        Args:
            nombre_carpeta (str): Nombre de la carpeta
            parent_folder_id (str, optional): ID de la carpeta padre
            
        Returns:
            dict: {'success': bool, 'message': str, 'folder_id': str}
        """
        try:
            file_metadata = {
                'name': nombre_carpeta,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'success': True,
                'message': f'Carpeta creada: {nombre_carpeta}',
                'folder_id': folder.get('id'),
                'folder_name': folder.get('name'),
                'web_view_link': folder.get('webViewLink')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al crear carpeta: {str(e)}'
            }
    
    def listar_archivos(self, folder_id=None, max_resultados=10):
        """
        Lista archivos en Drive
        
        Args:
            folder_id (str, optional): ID de carpeta específica (None = todos)
            max_resultados (int): Máximo de archivos a listar
            
        Returns:
            dict: {'success': bool, 'files': list, 'message': str}
        """
        try:
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_resultados,
                fields="files(id, name, mimeType, createdTime, modifiedTime, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'success': True,
                'files': files,
                'message': f'Se encontraron {len(files)} archivos'
            }
            
        except Exception as e:
            return {
                'success': False,
                'files': [],
                'message': f'Error al listar archivos: {str(e)}'
            }
    
    def eliminar_archivo(self, file_id):
        """
        Elimina un archivo de Drive
        
        Args:
            file_id (str): ID del archivo a eliminar
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return {
                'success': True,
                'message': f'Archivo {file_id} eliminado exitosamente'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al eliminar archivo: {str(e)}'
            }
    
    def compartir_archivo(self, file_id, email=None, role='reader', tipo='anyone'):
        """
        Comparte un archivo de Drive
        
        Args:
            file_id (str): ID del archivo a compartir
            email (str, optional): Email del usuario (si tipo='user')
            role (str): 'reader', 'writer', 'commenter'
            tipo (str): 'user', 'anyone', 'domain'
            
        Returns:
            dict: {'success': bool, 'message': str, 'permission_id': str}
        """
        try:
            permission = {
                'type': tipo,
                'role': role
            }
            
            if email and tipo == 'user':
                permission['emailAddress'] = email
            
            result = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            
            return {
                'success': True,
                'message': 'Archivo compartido exitosamente',
                'permission_id': result.get('id')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al compartir archivo: {str(e)}'
            }
    
    def _detectar_mime_type(self, ruta_archivo):
        """Detecta el tipo MIME de un archivo"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(ruta_archivo)
        
        if mime_type is None:
            # Tipos comunes para archivos sin extensión reconocida
            ext = os.path.splitext(ruta_archivo)[1].lower()
            mime_types_comunes = {
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
            }
            mime_type = mime_types_comunes.get(ext, 'application/octet-stream')
        
        return mime_type


# Funciones auxiliares para uso rápido
def subir_archivo_rapido(ruta_archivo, nombre_drive=None, credentials_file='credentials.json'):
    """
    Función auxiliar para subir archivos rápidamente
    
    Args:
        ruta_archivo (str): Ruta del archivo a subir
        nombre_drive (str, optional): Nombre en Drive
        credentials_file (str): Ruta a credentials.json
        
    Returns:
        dict: Resultado de la subida
    """
    uploader = GoogleDriveUploader(credentials_file=credentials_file)
    return uploader.subir_archivo(ruta_archivo, nombre_drive)


def subir_excel_a_drive(ruta_excel, nombre_drive=None, credentials_file='credentials.json'):
    """
    Función específica para subir archivos Excel a Drive
    
    Args:
        ruta_excel (str): Ruta del archivo Excel
        nombre_drive (str, optional): Nombre en Drive
        credentials_file (str): Ruta a credentials.json
        
    Returns:
        dict: Resultado de la subida
    """
    uploader = GoogleDriveUploader(credentials_file=credentials_file)
    return uploader.subir_archivo(
        ruta_excel,
        nombre_drive,
        mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
