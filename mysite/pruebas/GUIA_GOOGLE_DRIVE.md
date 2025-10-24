# 📤 Guía de Configuración - Google Drive Uploader

## 🎯 Objetivo
Esta guía te ayudará a configurar tu proyecto de Google Cloud para subir archivos a Google Drive.

---

## 📋 Requisitos Previos
- ✅ Cuenta de Google (Gmail)
- ✅ Proyecto en Google Cloud Console (ya lo tienes: `dogehoot`)
- ✅ Archivo `credentials.json` (ya lo tienes)

---

## 🔧 Configuración en Google Cloud Console

### Paso 1: Habilitar la API de Google Drive

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto: **dogehoot**
3. En el menú lateral, ve a **"APIs y servicios"** → **"Biblioteca"**
4. Busca: **"Google Drive API"**
5. Haz clic en **"Google Drive API"**
6. Presiona el botón **"HABILITAR"**

### Paso 2: Actualizar los Scopes OAuth

Tu archivo `credentials.json` ya está configurado, pero necesitas autorizar nuevos permisos:

1. Ve a **"APIs y servicios"** → **"Pantalla de consentimiento de OAuth"**
2. Haz clic en **"EDITAR APLICACIÓN"**
3. Ve a la sección **"Ámbitos"** (Scopes)
4. Haz clic en **"AGREGAR O QUITAR ÁMBITOS"**
5. Busca y selecciona estos ámbitos:
   - ✅ `../auth/drive.file` (Ver y administrar archivos de Google Drive que abres o creas con esta app)
   - ✅ `../auth/drive.appdata` (Ver, crear y eliminar su propia carpeta de datos de configuración de Google Drive)
6. Guarda los cambios

### Paso 3: Agregar Usuarios de Prueba (Modo Desarrollo)

Si tu app está en modo **"Testing"**:

1. Ve a **"Pantalla de consentimiento de OAuth"**
2. En la sección **"Usuarios de prueba"**
3. Haz clic en **"+ AGREGAR USUARIOS"**
4. Agrega los correos que usarás para probar:
   - `dogehootnotifications@gmail.com`
   - Tu correo personal
5. Guarda los cambios

---

## 🔑 Configuración de Credenciales

### Ejemplo de archivo `credentials.json`:

```json
{
  "installed": {
    "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "tu-proyecto",
    "client_secret": "TU_CLIENT_SECRET"
  }
}
```

✅ **Descarga tu propio `credentials.json` desde Google Cloud Console.**

---

## 🚀 Uso del Módulo

### Importar el módulo:

```python
from controladores.google_drive_uploader import GoogleDriveUploader

# Crear instancia
uploader = GoogleDriveUploader(credentials_file='credentials.json')

# Subir archivo
resultado = uploader.subir_archivo('reporte.xlsx', nombre_drive='Reporte_DogeHoot.xlsx')

if resultado['success']:
    print(f"✅ Archivo subido: {resultado['web_view_link']}")
else:
    print(f"❌ Error: {resultado['message']}")
```

---

## 🧪 Pruebas

### Ejecutar script de prueba:

```bash
cd mysite/pruebas
python test_google_drive.py
```

### Primera ejecución:
1. Se abrirá un navegador automáticamente
2. Inicia sesión con tu cuenta de Google
3. Acepta los permisos solicitados
4. Se creará automáticamente `token_drive.json`
5. Las siguientes ejecuciones no requerirán autenticación

---

## 📁 Estructura de Archivos

```
mysite/
├── credentials.json          # Credenciales OAuth (YA EXISTE)
├── token_drive.json         # Token de acceso (SE CREA AUTOMÁTICAMENTE)
├── controladores/
│   └── google_drive_uploader.py  # Módulo de subida (NUEVO)
└── pruebas/
    └── test_google_drive.py      # Script de prueba (NUEVO)
```

---

## 🔒 Seguridad

### Archivos a NO subir a GitHub:

Verifica que tu `.gitignore` incluya:

```
# Credenciales de Google
credentials.json
token.json
token_drive.json
old-token.json

# Variables de entorno
.env
```

---

## 🎮 Funciones Disponibles

### 1. Subir archivo desde disco
```python
uploader.subir_archivo('archivo.xlsx', nombre_drive='Mi_Archivo.xlsx')
```

### 2. Subir archivo desde memoria
```python
contenido = b'Datos en bytes'
uploader.subir_desde_memoria(contenido, 'archivo.txt', mime_type='text/plain')
```

### 3. Crear carpeta
```python
resultado = uploader.crear_carpeta('Reportes DogeHoot')
folder_id = resultado['folder_id']
```

### 4. Subir a carpeta específica
```python
uploader.subir_archivo('reporte.xlsx', folder_id='ID_DE_TU_CARPETA')
```

### 5. Listar archivos
```python
resultado = uploader.listar_archivos(max_resultados=10)
for archivo in resultado['files']:
    print(archivo['name'])
```

### 6. Compartir archivo públicamente
```python
uploader.compartir_archivo(file_id='ID_DEL_ARCHIVO', tipo='anyone', role='reader')
```

### 7. Eliminar archivo
```python
uploader.eliminar_archivo(file_id='ID_DEL_ARCHIVO')
```

---

## ❓ Solución de Problemas

### Error: "Access blocked: This app's request is invalid"
**Solución:** Verifica que hayas habilitado Google Drive API en Google Cloud Console

### Error: "invalid_scope"
**Solución:** Actualiza los scopes en la pantalla de consentimiento OAuth

### Error: "Token has been expired or revoked"
**Solución:** Elimina `token_drive.json` y vuelve a autenticarte

### Error: "FileNotFoundError: credentials.json"
**Solución:** Asegúrate de que `credentials.json` esté en la carpeta `mysite/`

---

## 🔄 Integración con Email Sender

### Ejemplo: Subir reporte y enviar link por email

```python
from controladores.google_drive_uploader import GoogleDriveUploader
from controladores.email_sender import EmailSender

# Subir a Drive
uploader = GoogleDriveUploader()
resultado_drive = uploader.subir_archivo('reporte.xlsx', nombre_drive='Reporte_DogeHoot.xlsx')

if resultado_drive['success']:
    # Compartir públicamente
    uploader.compartir_archivo(resultado_drive['file_id'], tipo='anyone', role='reader')
    
    # Enviar link por email
    email_sender = EmailSender()
    mensaje = f"""
    <h2>Tu reporte está listo</h2>
    <p>Ver en Drive: <a href="{resultado_drive['web_view_link']}">Abrir Reporte</a></p>
    """
    
    email_sender.enviar_correo_gmail(
        destinatario='usuario@gmail.com',
        asunto='Reporte DogeHoot',
        mensaje_html=mensaje
    )
```

---

## 📚 Recursos Adicionales

- [Documentación Google Drive API](https://developers.google.com/drive/api/v3/about-sdk)
- [Scopes de Google Drive](https://developers.google.com/drive/api/v3/about-auth)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**¡Listo! 🎉 Ahora puedes subir archivos a Google Drive desde DogeHoot.**
