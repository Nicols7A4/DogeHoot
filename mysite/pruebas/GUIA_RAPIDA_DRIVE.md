# 🚀 Guía Rápida - Google Drive en Local y PythonAnywhere

## ✅ El script ahora funciona automáticamente en ambos entornos

---

## 📋 PASO 1: Ejecutar en tu PC Local (PRIMERA VEZ)

### 1.1 Asegúrate de tener credentials.json

Coloca `credentials.json` en: `mysite/credentials.json`

```
DogeHoot-2/
└── mysite/
    ├── credentials.json  ← Aquí
    └── pruebas/
        └── test_google_drive.py
```

### 1.2 Ejecutar el script

```bash
cd mysite/pruebas
python test_google_drive.py
```

### 1.3 Autenticarte

- Se abrirá tu navegador automáticamente
- Inicia sesión con tu cuenta de Google
- Acepta los permisos
- ✅ Se creará `mysite/token_drive.json`

### 1.4 Verificar que funciona

Prueba cualquier opción del menú (ej: Opción 1 - Subida básica)

---

## 📤 PASO 2: Subir a PythonAnywhere

### 2.1 Archivos a subir

Necesitas subir estos 2 archivos a PythonAnywhere:

```
mysite/
├── credentials.json      ← SUBIR ESTE
└── token_drive.json     ← SUBIR ESTE
```

### 2.2 ¿Cómo subirlos?

**Opción A: Usando la interfaz web de PythonAnywhere**

1. Ve a `Files` en PythonAnywhere
2. Navega a `/home/tu_usuario/DogeHoot-2/mysite/`
3. Click en `Upload a file`
4. Sube `credentials.json`
5. Sube `token_drive.json`

**Opción B: Usando SCP (desde tu PC)**

```bash
scp mysite/credentials.json tu_usuario@ssh.pythonanywhere.com:/home/tu_usuario/DogeHoot-2/mysite/
scp mysite/token_drive.json tu_usuario@ssh.pythonanywhere.com:/home/tu_usuario/DogeHoot-2/mysite/
```

### 2.3 Verificar permisos

```bash
# En consola de PythonAnywhere
cd /home/tu_usuario/DogeHoot-2/mysite/
ls -la credentials.json token_drive.json

# Deberían aparecer ambos archivos
```

---

## 🧪 PASO 3: Probar en PythonAnywhere

### 3.1 Ejecutar el script

```bash
cd /home/tu_usuario/DogeHoot-2/mysite/pruebas
python3 test_google_drive.py
```

### 3.2 El script detecta automáticamente el entorno

Verás algo como:

```
🌐 Entorno detectado: PythonAnywhere
📂 Directorio base: /home/tu_usuario/DogeHoot-2/mysite

✅ credentials.json encontrado
✅ token_drive.json encontrado

🌐 DOGEHOOT - PRUEBA DE GOOGLE DRIVE UPLOADER
🌍 Entorno: PythonAnywhere

✅ Ejecutando en PythonAnywhere
   → Los tokens ya deben estar configurados
```

### 3.3 Probar subida

Selecciona opción 1 o 2 del menú para probar que funciona

---

## 🔒 SEGURIDAD - MUY IMPORTANTE

### ⚠️ NUNCA subas estos archivos a GitHub:

```gitignore
# Ya están en .gitignore:
mysite/credentials.json
mysite/token_drive.json
```

### ✅ Verificar .gitignore

```bash
# En tu PC, verifica que estén ignorados:
git status

# NO deben aparecer:
# - credentials.json
# - token_drive.json
```

---

## 🔄 Flujo Completo Resumido

```
┌─────────────────────┐
│   1. PC LOCAL       │
│   - Ejecutar script │
│   - Autenticarte    │
│   - Generar token   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   2. SUBIR A PA     │
│   - credentials.json│
│   - token_drive.json│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   3. PYTHONANYWHERE │
│   - Ejecutar script │
│   - ¡Ya funciona!   │
└─────────────────────┘
```

---

## 🆘 Solución de Problemas

### Error: "credentials.json NO encontrado"

**Solución:** Sube el archivo a `/home/tu_usuario/DogeHoot-2/mysite/`

### Error: "token_drive.json NO encontrado"

**Solución:** 
1. Ejecuta el script en tu PC primero
2. Se generará automáticamente
3. Súbelo a PythonAnywhere

### Error: "Token has been expired or revoked"

**Solución:**
1. Borra `token_drive.json` en tu PC
2. Ejecuta el script de nuevo
3. Auténticate de nuevo
4. Sube el nuevo `token_drive.json` a PythonAnywhere

### Error: "Access blocked" al hacer push

**Solución:** Asegúrate de que `.gitignore` incluya:
```
mysite/credentials.json
mysite/token_drive.json
```

---

## 📊 Usar en tu Aplicación Flask

```python
from controladores.google_drive_uploader import GoogleDriveUploader
import os

# Detectar entorno
def es_pythonanywhere():
    return 'PYTHONANYWHERE_SITE' in os.environ

# Configurar rutas
if es_pythonanywhere():
    user = os.environ.get('USER')
    base_dir = f'/home/{user}/DogeHoot-2/mysite'
else:
    base_dir = os.path.abspath('.')

credentials = os.path.join(base_dir, 'credentials.json')
token = os.path.join(base_dir, 'token_drive.json')

# Usar el uploader
uploader = GoogleDriveUploader(
    credentials_file=credentials,
    token_file=token
)

# Subir archivo
resultado = uploader.subir_archivo('reporte.xlsx')
if resultado['success']:
    print(f"Link: {resultado['web_view_link']}")
```

---

## ✅ Checklist Final

### En tu PC:
- [ ] `credentials.json` en `mysite/`
- [ ] Ejecutar `test_google_drive.py`
- [ ] Autenticarte en navegador
- [ ] Verificar que se creó `token_drive.json`
- [ ] Probar que funciona (subir archivo de prueba)

### En PythonAnywhere:
- [ ] Subir `credentials.json`
- [ ] Subir `token_drive.json`
- [ ] Ejecutar `test_google_drive.py`
- [ ] Verificar que detecta PythonAnywhere
- [ ] Probar subida de archivo

### Seguridad:
- [ ] Verificar `.gitignore`
- [ ] Confirmar que tokens NO están en GitHub
- [ ] Hacer commit solo del código, no de tokens

---

**¡Listo! Ahora el mismo script funciona en ambos entornos automáticamente 🎉**
