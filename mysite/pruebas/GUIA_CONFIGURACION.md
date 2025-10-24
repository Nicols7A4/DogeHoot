# ============================================
# GUÍA RÁPIDA: CONFIGURACIÓN DE CORREOS
# ============================================

## 🎯 RESUMEN EJECUTIVO

Para enviar correos desde tu aplicación DogeHoot en PythonAnywhere necesitas:

### ✅ LO QUE SÍ FUNCIONA
- **Gmail**: Totalmente funcional
- **SMTP Gmail**: smtp.gmail.com:587 está en la whitelist

### ❌ LO QUE NO FUNCIONA (en PythonAnywhere gratuito)
- **Hotmail/Outlook SMTP**: Bloqueado
- **Alternativa**: Microsoft Graph API (más complejo)

---

## 📝 PASOS PARA CONFIGURAR GMAIL

### 1. Preparar tu cuenta Gmail

```
1. Ve a: https://myaccount.google.com/security
2. Activa "Verificación en dos pasos"
3. Ve a "Contraseñas de aplicaciones"
4. Genera una contraseña para "Correo"
5. Guarda el código de 16 caracteres
```

### 2. Configurar archivo .env

```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env y agrega:
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 3. Instalar dependencias

```bash
pip install python-dotenv openpyxl
```

### 4. Probar

```bash
python test_enviar_correo.py
```

---

## 🔄 ALTERNATIVA PARA HOTMAIL/OUTLOOK

Ya que SMTP de Outlook está bloqueado en PythonAnywhere gratuito, tienes 3 opciones:

### Opción 1: Usar solo Gmail (RECOMENDADO)
```python
# Enviar todo por Gmail, sin importar si es Drive o OneDrive
sender.enviar_correo_gmail(
    destinatario='usuario@hotmail.com',  # Puede ser cualquier correo
    asunto='Reporte DogeHoot',
    mensaje_html=mensaje,
    archivo_adjunto='reporte.xlsx'
)
```

### Opción 2: Microsoft Graph API
- Más complejo de configurar
- Requiere registrar app en Azure
- Necesita OAuth2
- Funciona en PythonAnywhere gratuito

### Opción 3: Pagar PythonAnywhere
- Desbloquea más servidores SMTP
- Cuesta $5/mes mínimo

---

## 💡 RECOMENDACIÓN PARA TU PROYECTO

```python
# Arquitectura recomendada:

def enviar_reporte(email_destino, archivo_excel, servicio):
    """
    Envía reporte por Gmail siempre
    El 'servicio' (drive/onedrive) solo afecta el mensaje
    """
    sender = EmailSender()
    
    # Personalizar mensaje según servicio
    if servicio == 'drive':
        mensaje = "Tu reporte estará disponible en Google Drive"
    else:
        mensaje = "Tu reporte estará disponible en OneDrive"
    
    # SIEMPRE enviar por Gmail
    return sender.enviar_correo_gmail(
        destinatario=email_destino,
        asunto=f'Reporte DogeHoot ({servicio})',
        mensaje_html=mensaje,
        archivo_adjunto=archivo_excel
    )
```

---

## 🔒 SEGURIDAD

### ✅ HACER
- Usar contraseñas de aplicación
- Agregar .env a .gitignore
- Revocar contraseñas si se comprometen
- Validar emails de destino

### ❌ NO HACER
- Usar contraseña real de Gmail
- Subir .env a GitHub
- Hard-codear credenciales
- Compartir contraseñas de aplicación

---

## 📊 FLUJO COMPLETO RECOMENDADO

```
1. Usuario solicita reporte
   ↓
2. Generar Excel con datos
   ↓
3. Subir a Drive/OneDrive (tu API)
   ↓
4. Obtener link compartido
   ↓
5. Enviar correo por Gmail con:
   - Link al archivo
   - Archivo adjunto (opcional)
   - Instrucciones
```

---

## 🚀 PARA PRODUCCIÓN

Cuando despliegues en PythonAnywhere:

```python
# mysite/config.py
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_CONFIG = {
    'gmail_user': os.getenv('GMAIL_USER'),
    'gmail_password': os.getenv('GMAIL_APP_PASSWORD'),
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}
```

```python
# mysite/utils/email_sender.py
from config import EMAIL_CONFIG

class ProductionEmailSender:
    # Tu código aquí usando EMAIL_CONFIG
```

---

## 📞 TROUBLESHOOTING

### Error: SMTPAuthenticationError
```
Causa: Contraseña incorrecta o no es contraseña de aplicación
Solución: Genera nueva contraseña de aplicación
```

### Error: Connection timeout
```
Causa: Firewall o SMTP bloqueado
Solución: Verifica whitelist de PythonAnywhere
```

### Email no llega
```
Causa: Puede estar en spam
Solución: 
1. Revisa carpeta de spam
2. Agrega remitente a contactos
3. Verifica que el email sea válido
```

---

## 📚 RECURSOS

- [Gmail App Passwords](https://myaccount.google.com/apppasswords)
- [PythonAnywhere Whitelist](https://help.pythonanywhere.com/pages/SMTPForFreeUsers)
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview)

---

## ✨ PRÓXIMOS PASOS

1. ✅ Configurar Gmail
2. ✅ Probar envío básico
3. 🔜 Integrar con generador de reportes
4. 🔜 Implementar APIs de Drive/OneDrive
5. 🔜 Crear interfaz de usuario
6. 🔜 Desplegar en PythonAnywhere
