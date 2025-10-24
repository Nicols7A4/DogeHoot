# 📧 Sistema de Envío de Correos - DogeHoot

Este directorio contiene las pruebas para el sistema de envío de correos electrónicos con reportes Excel.

## 📋 Archivos

- **`.env.example`**: Plantilla de configuración con ejemplos
- **`.env`**: Tu archivo real con credenciales (NO subir a GitHub)
- **`email_sender_test.py`**: Módulo principal para envío de correos
- **`test_enviar_correo.py`**: Script de pruebas interactivo
- **`requirements_pruebas.txt`**: Dependencias necesarias

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements_pruebas.txt
```

### 2. Configurar credenciales

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales reales
```

### 3. Obtener contraseñas de aplicación

#### Para Gmail:
1. Ve a https://myaccount.google.com/security
2. Activa la verificación en 2 pasos
3. Busca "Contraseñas de aplicaciones"
4. Genera una nueva para "Correo"
5. Copia el código de 16 caracteres en `.env`

#### Para Hotmail:
1. Ve a https://account.microsoft.com/security
2. Activa la verificación en 2 pasos
3. Busca "Seguridad avanzada" > "Contraseñas de aplicaciones"
4. Genera una nueva
5. Copia el código en `.env`

## 🧪 Ejecutar pruebas

```bash
python test_enviar_correo.py
```

El script te mostrará un menú interactivo con opciones:
1. Probar envío simple con Gmail (sin adjunto)
2. Probar envío con Gmail + archivo Excel
3. Probar envío con Hotmail + archivo Excel
4. Ejecutar todas las pruebas

## ⚠️ Limitaciones de PythonAnywhere Gratuito

### ✅ Gmail - FUNCIONA
- Servidor SMTP: `smtp.gmail.com:587`
- Estado: **Permitido** en PythonAnywhere gratuito
- Recomendación: **Usar este para producción**

### ❌ Hotmail/Outlook - BLOQUEADO
- Servidor SMTP: `smtp-mail.outlook.com:587`
- Estado: **Bloqueado** en PythonAnywhere gratuito
- Alternativas:
  - Usar Microsoft Graph API (más complejo)
  - Actualizar a cuenta de pago de PythonAnywhere
  - Usar solo Gmail para ambos servicios

## 📊 Uso del módulo en tu código

```python
from email_sender_test import EmailSender

# Crear instancia
sender = EmailSender()

# Enviar con Gmail
resultado = sender.enviar_reporte_excel(
    destinatario='usuario@gmail.com',
    tipo_servicio='drive',  # Para Google Drive
    archivo_excel='ruta/al/reporte.xlsx'
)

# Enviar con Hotmail (si está disponible)
resultado = sender.enviar_reporte_excel(
    destinatario='usuario@hotmail.com',
    tipo_servicio='onedrive',  # Para OneDrive
    archivo_excel='ruta/al/reporte.xlsx'
)

# Verificar resultado
if resultado['success']:
    print(f"✅ {resultado['message']}")
else:
    print(f"❌ {resultado['message']}")
```

## 🔐 Seguridad

- **NUNCA** subas el archivo `.env` a GitHub
- Usa contraseñas de aplicación, NO tu contraseña real
- Las contraseñas de aplicación tienen permisos limitados
- Si sospechas que tu contraseña fue comprometida, revócala inmediatamente

## 📝 Notas adicionales

### Estructura del mensaje
Los correos incluyen:
- Asunto personalizado según el servicio
- Mensaje HTML con formato profesional
- Archivo Excel adjunto
- Información de la fecha de generación

### Próximos pasos
Para la integración completa con Drive/OneDrive, necesitarás:
1. APIs de Google Drive / Microsoft Graph
2. Tokens OAuth2
3. Lógica para subir archivos y compartir

## 🐛 Solución de problemas

### Error: "Authentication failed"
- Verifica que usas contraseña de aplicación, no la contraseña normal
- Asegúrate de tener verificación en 2 pasos activada

### Error: "Connection refused" (Hotmail)
- Es normal en PythonAnywhere gratuito
- El servidor SMTP de Outlook está bloqueado
- Usa Gmail o actualiza tu cuenta

### Error: "Module not found"
- Ejecuta: `pip install -r requirements_pruebas.txt`

## 📞 Contacto

Si tienes problemas, revisa:
- Configuración del archivo `.env`
- Permisos de la cuenta de correo
- Logs del script de prueba
