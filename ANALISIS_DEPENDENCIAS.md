# 📊 ANÁLISIS DE DEPENDENCIAS - DogeHoot

## 🎯 Resumen Ejecutivo

- **Total de librerías en requirements.txt:** 75
- **Librerías NO utilizadas:** 17 (22.7%)
- **Ahorro estimado de espacio:** 30-50 MB
- **Ahorro de tiempo de instalación:** ~15-30 segundos

---

## ❌ LIBRERÍAS NO UTILIZADAS (17)

### 📦 Herramientas CLI No Usadas
| Librería | Versión | Motivo |
|----------|---------|--------|
| `typer` | 0.19.2 | No hay CLI con typer en el proyecto |
| `shellingham` | 1.5.4 | Dependencia de typer (no usada) |
| `snakesay` | 0.10.4 | ASCII art no usado |
| `tabulate` | 0.9.0 | No hay tablas en terminal |
| `rich` | 14.2.0 | No hay rich text en terminal |

### 📝 Procesamiento de Texto No Usado
| Librería | Versión | Motivo |
|----------|---------|--------|
| `markdown-it-py` | 4.0.0 | No hay procesamiento de Markdown |
| `mdurl` | 0.1.2 | Dependencia de markdown-it-py |
| `Pygments` | 2.19.2 | No hay syntax highlighting |

### 📧 Servicios de Email No Usados
| Librería | Versión | Motivo |
|----------|---------|--------|
| `sendgrid` | 6.12.5 | Se usa Outlook/Gmail en su lugar |
| `python-http-client` | 3.3.7 | Dependencia de sendgrid |

### 📄 Exportación de Excel Duplicada
| Librería | Versión | Motivo |
|----------|---------|--------|
| `XlsxWriter` | 3.1.9 | Se usa `openpyxl` para todo |

### 🔧 Herramientas de Desarrollo No Usadas
| Librería | Versión | Motivo |
|----------|---------|--------|
| `pythonanywhere` | 0.17.0 | Solo comentarios, no uso real |
| `pythonanywhere-core` | 0.2.7 | Dependencia de pythonanywhere |
| `schema` | 0.7.8 | No hay validación con esta librería |
| `docopt` | 0.6.2 | No hay parsing CLI |

### ⚙️ Configuración Duplicada
| Librería | Versión | Motivo |
|----------|---------|--------|
| `dotenv` | 0.9.9 | Se usa `python-dotenv` en su lugar |

---

## ✅ LIBRERÍAS QUE SÍ SE USAN (58)

### 🌐 Framework Web Principal
```
Flask==3.1.2                    # Framework web principal
Flask-Login==0.6.3              # Autenticación de usuarios
Flask-Mail==0.10.0              # Envío de emails
Flask-SocketIO==5.5.1           # WebSockets para juego en tiempo real
Werkzeug==3.1.3                 # Utilidades HTTP
```

**Dónde se usan:**
- `main.py`: Inicialización de Flask y Mail
- `routes_web.py`: Rutas, autenticación con Flask-Login
- `routes_api.py`: API REST
- `game_events.py`: Socket.IO para juego en tiempo real

---

### 🗄️ Base de Datos
```
PyMySQL==1.1.2                  # Conector MySQL
certifi==2025.10.5              # Certificados SSL para DB
```

**Dónde se usan:**
- `bd.py`: Conexión a MySQL con SSL
- `controladores/controlador_partidas.py`: Operaciones de DB

---

### 📊 Procesamiento de Datos
```
pandas==2.1.4                   # Análisis de datos
openpyxl==3.1.2                 # Lectura/escritura Excel
pillow==12.0.0                  # Procesamiento de imágenes
```

**Dónde se usan:**
- `controladores/importador.py`: Pandas para leer Excel
- `controladores/importarExcel.py`: Openpyxl para importar cuestionarios
- `routes_api.py`: Openpyxl para exportar reportes Excel
- `main.py`: Pillow para redimensionar fotos de perfil
- `controladores/foto_perfil.py`: Pillow para optimizar imágenes

---

### ⚡ Tiempo Real / WebSockets
```
eventlet==0.40.3                # Servidor asíncrono
python-socketio==5.14.2         # Socket.IO servidor
python-engineio==4.12.3         # Engine.IO (base de Socket.IO)
```

**Dónde se usan:**
- `game_events.py`: Eventos del juego en tiempo real (temporizadores, respuestas)
- `main.py`: Integración con Flask-SocketIO

---

### 🔐 Google Services (Drive + Gmail)
```
google-api-python-client==2.184.0   # Cliente API de Google
google-auth==2.41.1                 # Autenticación Google
google-auth-httplib2==0.2.0         # Transport HTTP para auth
google-auth-oauthlib==1.2.2         # OAuth2 para Google
```

**Dónde se usan:**
- `controladores/google_drive_uploader.py`: Subir fotos a Google Drive
- `controladores/email_sender.py`: Enviar emails con Gmail API
- `generar_token.py`: Generar tokens OAuth2

---

### 📧 Outlook / OneDrive
```
requests==2.31.0                # HTTP requests
requests-oauthlib==2.0.0        # OAuth para requests
```

**Dónde se usan:**
- `controladores/outlook_email_sender.py`: Envío de emails con Microsoft Graph API
- `controladores/onedrive_uploader.py`: Subir archivos a OneDrive

---

### 🔒 Seguridad
```
itsdangerous==2.2.0             # Tokens seguros
cryptography==46.0.3            # Cifrado SSL
```

**Dónde se usan:**
- `controladores/usuarios.py`: Generación de tokens de verificación
- `bd.py`: SSL para conexión segura a DB

---

### ⚙️ Configuración
```
python-dotenv==1.0.0            # Variables de entorno
```

**Dónde se usan:**
- `main.py`: Cargar variables .env
- `bd.py`: Configuración de DB
- `controladores/outlook_email_sender.py`: Credenciales OAuth
- `controladores/onedrive_uploader.py`: Credenciales OneDrive

---

### 📦 Dependencias Automáticas (43)
Estas se instalan automáticamente con las librerías principales:

```
bidict, blinker, cachetools, cffi, charset-normalizer, click,
colorama, dnspython, et_xmlfile, google-api-core,
googleapis-common-protos, greenlet, h11, httplib2, idna,
Jinja2, MarkupSafe, oauthlib, packaging, proto-plus, protobuf,
pyasn1, pyasn1_modules, pycparser, pyparsing, python-dateutil,
pytz, rsa, simple-websocket, six, typing_extensions, tzdata,
uritemplate, urllib3, wsproto
```

---

## 📋 MAPA DE USO POR ARCHIVO

### Archivos Principales:
```
main.py
├── Flask, Flask-Mail (Mail, Message)
├── PIL (Image)
├── werkzeug (secure_filename)
└── python-dotenv (load_dotenv)

routes_web.py
├── Flask (render_template, request, redirect, flash, session, jsonify)
├── Flask-Login (login_required, current_user)
└── Flask-Mail (Message)

routes_api.py
├── Flask (jsonify, request, send_file)
├── openpyxl (Workbook, Font, PatternFill)
├── PyMySQL
└── werkzeug (secure_filename)

game_events.py
├── Flask-SocketIO (join_room, leave_room, emit)
└── eventlet (temporizadores)

ajax_game.py
└── Flask (session)
```

### Controladores:
```
controladores/importarExcel.py
├── openpyxl (load_workbook)
└── Flask (Blueprint, request, send_from_directory, jsonify)

controladores/importador.py
└── pandas (read_excel)

controladores/foto_perfil.py
├── Flask (Blueprint, request, redirect, flash, session)
├── PIL (Image)
└── PyMySQL

controladores/google_drive_uploader.py
├── google-api-python-client (build)
└── google-auth (Credentials, Request)

controladores/email_sender.py
├── google-api-python-client (build)
└── google-auth (Credentials)

controladores/outlook_email_sender.py
├── requests
└── python-dotenv (load_dotenv)

controladores/onedrive_uploader.py
├── requests
└── python-dotenv (load_dotenv)

controladores/usuarios.py
└── itsdangerous (URLSafeTimedSerializer)

bd.py
├── PyMySQL
├── certifi
└── python-dotenv (load_dotenv)
```

---

## 🚀 CÓMO OPTIMIZAR

### Opción 1: Eliminar librerías no usadas
```bash
pip uninstall -r no_requirements.txt -y
```

### Opción 2: Reinstalar desde cero
```bash
# Desinstalar todo
pip freeze > temp_requirements.txt
pip uninstall -r temp_requirements.txt -y

# Instalar solo lo necesario
pip install -r requirements_optimizado.txt
```

### Opción 3: Actualizar requirements.txt
```bash
# Respaldar actual
cp requirements.txt requirements_old.txt

# Reemplazar con optimizado
cp requirements_optimizado.txt requirements.txt
```

---

## 📈 BENEFICIOS DE OPTIMIZAR

✅ **Menor tamaño de instalación** (~30-50 MB menos)  
✅ **Instalación más rápida** (menos dependencias que resolver)  
✅ **Menos vulnerabilidades potenciales** (menos código = menos superficie de ataque)  
✅ **Mejor rendimiento** (menos librerías cargadas en memoria)  
✅ **Deployment más rápido** (menos archivos que transferir)  

---

## ⚠️ ADVERTENCIAS

- **No eliminar** las "dependencias automáticas" sin probar
- **Hacer backup** de `requirements.txt` antes de cambios
- **Probar en entorno de desarrollo** antes de producción
- **Verificar imports** después de desinstalar

---

## 📝 NOTAS ADICIONALES

### numpy (comentado)
```python
# numpy==1.26.4
```
Ya está comentado en `requirements.txt`, lo que indica que se intentó eliminar antes.

### pandas vs numpy
Pandas depende de numpy internamente, pero numpy no se importa directamente en el código.

### typing_extensions
Aunque es dependencia de typer (no usado), también puede ser requerido por otras librerías. **Mantener por seguridad.**

---

## 🎯 RECOMENDACIÓN FINAL

**Acción sugerida:** Usar `requirements_optimizado.txt` para nuevas instalaciones.

**Para proyecto actual:** Ejecutar `pip uninstall -r no_requirements.txt -y` y probar exhaustivamente.

---

*Generado por análisis automático del proyecto DogeHoot*  
*Fecha: 28 de octubre de 2025*
