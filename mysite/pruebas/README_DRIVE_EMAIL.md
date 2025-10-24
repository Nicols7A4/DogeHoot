# 🚀 DogeHoot - Sistema de Reportes y Almacenamiento

## 📦 Módulos Disponibles

### 1. 📧 Email Sender
Envío de correos con Gmail y Hotmail (Outlook)

**Ubicación:** `mysite/controladores/email_sender.py`

**Características:**
- ✅ Envío de correos por Gmail
- ✅ Envío de correos por Hotmail/Outlook
- ✅ Soporte para archivos adjuntos
- ✅ Mensajes HTML personalizados
- ✅ Plantillas para reportes

### 2. 📤 Google Drive Uploader
Subida de archivos a Google Drive

**Ubicación:** `mysite/controladores/google_drive_uploader.py`

**Características:**
- ✅ Subir archivos desde disco
- ✅ Subir archivos desde memoria
- ✅ Crear carpetas
- ✅ Listar archivos
- ✅ Compartir archivos públicamente
- ✅ Eliminar archivos
- ✅ Soporte para múltiples tipos de archivo

---

## 🔧 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en `mysite/pruebas/` con:

```env
# Gmail
GMAIL_USER=tu_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Hotmail (Opcional)
HOTMAIL_USER=tu_email@hotmail.com
HOTMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 3. Configurar Google Drive

1. Coloca `credentials.json` en `mysite/`
2. Habilita Google Drive API en Google Cloud Console
3. Lee la guía completa: `mysite/pruebas/GUIA_GOOGLE_DRIVE.md`

---

## 💻 Uso Rápido

### Enviar correo simple

```python
from controladores.email_sender import EmailSender

sender = EmailSender()
resultado = sender.enviar_correo_gmail(
    destinatario='usuario@gmail.com',
    asunto='Prueba',
    mensaje_html='<h1>¡Hola desde DogeHoot!</h1>'
)

print(resultado['message'])
```

### Subir archivo a Drive

```python
from controladores.google_drive_uploader import GoogleDriveUploader

uploader = GoogleDriveUploader()
resultado = uploader.subir_archivo('reporte.xlsx')

if resultado['success']:
    print(f"Link: {resultado['web_view_link']}")
```

### Ejemplo completo (Drive + Email)

```python
from controladores.google_drive_uploader import GoogleDriveUploader
from controladores.email_sender import EmailSender

# 1. Subir a Drive
uploader = GoogleDriveUploader()
resultado_drive = uploader.subir_archivo('reporte.xlsx')

# 2. Compartir públicamente
uploader.compartir_archivo(resultado_drive['file_id'], tipo='anyone')

# 3. Enviar link por email
sender = EmailSender()
mensaje = f'<a href="{resultado_drive["web_view_link"]}">Ver Reporte</a>'
sender.enviar_correo_gmail('usuario@gmail.com', 'Reporte Listo', mensaje)
```

---

## 🧪 Scripts de Prueba

### Test Email Sender
```bash
cd mysite/pruebas
python test_enviar_correo.py
```

### Test Google Drive
```bash
cd mysite/pruebas
python test_google_drive.py
```

### Ejemplo Completo
```bash
cd mysite/pruebas
python ejemplo_drive_email.py
```

---

## 📁 Estructura de Archivos

```
mysite/
├── credentials.json              # Credenciales OAuth (NO SUBIR A GIT)
├── token_drive.json             # Token Drive (SE CREA AUTO)
├── controladores/
│   ├── email_sender.py          # ✅ Módulo de emails
│   └── google_drive_uploader.py # ✅ Módulo de Drive
└── pruebas/
    ├── .env                     # Variables de entorno (NO SUBIR A GIT)
    ├── test_enviar_correo.py    # 🧪 Test emails
    ├── test_google_drive.py     # 🧪 Test Drive
    ├── ejemplo_drive_email.py   # 📋 Ejemplo completo
    ├── GUIA_CONFIGURACION.md    # 📖 Guía emails
    ├── GUIA_GOOGLE_DRIVE.md     # 📖 Guía Drive
    └── README_CORREOS.md        # 📖 Info correos
```

---

## 🔐 Seguridad

### Archivos protegidos en `.gitignore`:

```gitignore
# Credenciales
credentials.json
token.json
token_drive.json
.env
mysite/.env
mysite/pruebas/.env
```

### ⚠️ NUNCA subas a Git:
- ❌ `credentials.json`
- ❌ `token*.json`
- ❌ `.env`
- ❌ Contraseñas de aplicación

---

## 📚 Guías Completas

- 📧 **Email:** `mysite/pruebas/GUIA_CONFIGURACION.md`
- 📤 **Drive:** `mysite/pruebas/GUIA_GOOGLE_DRIVE.md`
- 📖 **Correos:** `mysite/pruebas/README_CORREOS.md`

---

## 🎯 Casos de Uso

### 1. Enviar reporte por email
```python
sender = EmailSender()
sender.enviar_reporte_excel(
    destinatario='usuario@gmail.com',
    tipo_servicio='drive',  # 'drive' o 'onedrive'
    archivo_excel='reporte.xlsx'
)
```

### 2. Guardar reporte en Drive
```python
uploader = GoogleDriveUploader()
resultado = uploader.subir_excel_a_drive('reporte.xlsx')
```

### 3. Crear carpeta y subir múltiples archivos
```python
uploader = GoogleDriveUploader()

# Crear carpeta
carpeta = uploader.crear_carpeta('Reportes DogeHoot')
folder_id = carpeta['folder_id']

# Subir archivos a la carpeta
for archivo in ['reporte1.xlsx', 'reporte2.xlsx']:
    uploader.subir_archivo(archivo, folder_id=folder_id)
```

### 4. Listar reportes subidos
```python
uploader = GoogleDriveUploader()
resultado = uploader.listar_archivos(max_resultados=20)

for archivo in resultado['files']:
    print(f"{archivo['name']} - {archivo['webViewLink']}")
```

---

## ❓ Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Error: "ModuleNotFoundError: No module named 'openpyxl'"
```bash
pip install openpyxl
```

### Error: "Access blocked" en Google Drive
- Habilita Google Drive API en Google Cloud Console
- Agrega los scopes correctos en la pantalla de consentimiento OAuth

### Error: "SMTP Authentication Error"
- Verifica que uses contraseñas de aplicación (no tu contraseña normal)
- Verifica que la verificación en 2 pasos esté activada

---

## 📊 Dependencias Instaladas

```txt
python-dotenv==1.0.1      # Variables de entorno
openpyxl==3.1.5          # Archivos Excel
google-api-python-client  # Google Drive API
google-auth              # Autenticación Google
Flask-Mail               # Envío de emails
```

---

## 🎮 Próximos Pasos

1. ✅ Configurar credenciales de email y Drive
2. ✅ Probar scripts de prueba
3. 🔄 Integrar con tu sistema de reportes de partidas
4. 🚀 Automatizar envío de reportes

---

## 🤝 Soporte

Si tienes problemas:

1. Lee las guías en `mysite/pruebas/`
2. Revisa los archivos de ejemplo
3. Verifica tu configuración en Google Cloud Console
4. Asegúrate de tener las contraseñas de aplicación correctas

---

**¡Listo para generar y compartir reportes! 🎉**
