# ✅ Validaciones Mejoradas para Importación de Excel

## 🎯 Validaciones Implementadas

### 1. **Validación de Encabezados (Columnas Requeridas)**

El sistema ahora verifica que el archivo Excel tenga **TODAS** las columnas obligatorias:

```
✅ pregunta
✅ opcion_1
✅ opcion_2
✅ opcion_3
✅ opcion_4
✅ opcion_c_orrecta
✅ tiempo_segundos
🔹 url_imagen (opcional)
```

**Error si falta alguna:**
```
❌ "Faltan las siguientes columnas requeridas: opcion_4, tiempo_segundos. 
    Verifica que el archivo tenga TODAS las columnas obligatorias."
```

**Nota:** Los nombres de columnas ahora son **case-insensitive** (no importa si están en mayúsculas o minúsculas).

---

### 2. **Validación de Filas Vacías**

✅ El sistema **ignora automáticamente** filas completamente vacías
- No genera errores
- No detiene la importación
- Útil cuando hay espacios en blanco en el Excel

---

### 3. **Validación por Fila**

Para cada fila del Excel, se valida:

#### 📝 **Pregunta**
```python
❌ Error: "Fila 5: La pregunta está vacía."
```
- No puede estar vacía
- Debe tener al menos un carácter

---

#### ⏱️ **Tiempo (tiempo_segundos)**
```python
❌ Error: "Fila 3: El campo 'tiempo_segundos' está vacío."
❌ Error: "Fila 7: Tiempo inválido 'abc'. Debe ser un número entero entre 10 y 100."
❌ Error: "Fila 9: El tiempo debe estar entre 10 y 100 segundos (recibido: 5)."
```

**Reglas:**
- ✅ Debe ser un número entero
- ✅ Rango válido: **10 a 100 segundos**
- ❌ No puede estar vacío
- ❌ No puede ser texto

---

#### ✔️ **Opción Correcta (opcion_c_orrecta)**
```python
❌ Error: "Fila 4: El campo 'opcion_c_orrecta' está vacío."
❌ Error: "Fila 6: Opción correcta inválida '5'. Debe ser un número del 1 al 4."
❌ Error: "Fila 8: El índice de opción correcta debe ser 1, 2, 3 o 4 (recibido: 0)."
```

**Reglas:**
- ✅ Debe ser un número entero
- ✅ Valores válidos: **1, 2, 3 o 4**
- ❌ No puede estar vacío
- ❌ No puede ser texto
- ❌ No puede ser 0 o mayor que 4

---

#### 📋 **Opciones (opcion_1 a opcion_4)**
```python
❌ Error: "Fila 10: Se necesitan al menos 2 opciones con texto. Solo se encontraron 1."
❌ Error: "Fila 12: La opción correcta (opcion_3) está vacía. 
           Debes escribir un texto para esa opción."
```

**Reglas:**
- ✅ Al menos **2 opciones** deben tener texto (1 correcta + 1 incorrecta mínimo)
- ✅ La opción marcada como correcta **NO puede estar vacía**
- ✅ Puedes dejar opciones vacías (opcion_3 y opcion_4 pueden estar en blanco si tienes al menos 2 opciones)

**Ejemplo válido:**
| pregunta | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta | tiempo_segundos |
|----------|----------|----------|----------|----------|------------------|-----------------|
| ¿Qué es Python? | Un lenguaje | Una serpiente | *vacío* | *vacío* | 1 | 15 |

✅ **OK** - Tiene 2 opciones y la correcta (1) tiene texto

**Ejemplo inválido:**
| pregunta | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta | tiempo_segundos |
|----------|----------|----------|----------|----------|------------------|-----------------|
| ¿Qué es Python? | Un lenguaje | *vacío* | *vacío* | *vacío* | 2 | 15 |

❌ **ERROR** - La opción correcta (2) está vacía

---

#### 🖼️ **URL de Imagen (url_imagen) - OPCIONAL**
```python
⚠️  Warning: "Fila 14: URL de imagen inválida 'imagen.png'. 
            Debe empezar con http:// o https://"
```

**Reglas:**
- ✅ Puede estar vacía (es opcional)
- ✅ Si tiene valor, debe empezar con `http://` o `https://`
- ⚠️ Si es inválida, se muestra un warning pero **no detiene la importación**

---

## 📊 Ejemplos de Respuesta

### ✅ **Importación Exitosa**
```json
{
  "success": true,
  "message": "5 preguntas importadas y listas para guardar.",
  "preguntas_actualizadas": [...]
}
```

Mensaje en pantalla:
```
✅ 5 preguntas importadas con éxito. Las preguntas han reemplazado las anteriores. 
   Usa "Guardar cambios" para persistir en la base de datos.
```

---

### ❌ **Errores de Validación (Múltiples)**
```json
{
  "success": false,
  "error": "Se encontraron 4 error(es) en el archivo:",
  "errores": [
    "Fila 3: El tiempo debe estar entre 10 y 100 segundos (recibido: 5).",
    "Fila 5: La pregunta está vacía.",
    "Fila 7: La opción correcta (opcion_2) está vacía. Debes escribir un texto para esa opción.",
    "Fila 9: Opción correcta inválida 'abc'. Debe ser un número del 1 al 4."
  ]
}
```

Mensaje en pantalla:
```
❌ Se encontraron 4 error(es) en el archivo:

1. Fila 3: El tiempo debe estar entre 10 y 100 segundos (recibido: 5).
2. Fila 5: La pregunta está vacía.
3. Fila 7: La opción correcta (opcion_2) está vacía. Debes escribir un texto para esa opción.
4. Fila 9: Opción correcta inválida 'abc'. Debe ser un número del 1 al 4.
```

---

## 🧪 Casos de Prueba

### **Caso 1: Columnas faltantes**
```
Excel sin la columna "tiempo_segundos"
→ ❌ Error inmediato antes de procesar filas
```

### **Caso 2: Fila con opción correcta vacía**
```
pregunta: "¿Qué es Flask?"
opcion_1: "Framework"
opcion_2: "" (vacío)
opcion_3: "Base de datos"
opcion_c_orrecta: 2
→ ❌ Error: "La opción correcta (opcion_2) está vacía"
```

### **Caso 3: Solo una opción con texto**
```
pregunta: "¿Qué es Python?"
opcion_1: "Un lenguaje"
opcion_2: "" (vacío)
opcion_3: "" (vacío)
opcion_4: "" (vacío)
opcion_c_orrecta: 1
→ ❌ Error: "Se necesitan al menos 2 opciones con texto. Solo se encontraron 1."
```

### **Caso 4: Tiempo fuera de rango**
```
tiempo_segundos: 150
→ ❌ Error: "El tiempo debe estar entre 10 y 100 segundos (recibido: 150)."

tiempo_segundos: 5
→ ❌ Error: "El tiempo debe estar entre 10 y 100 segundos (recibido: 5)."
```

### **Caso 5: Índice de opción correcta inválido**
```
opcion_c_orrecta: 0
→ ❌ Error: "El índice de opción correcta debe ser 1, 2, 3 o 4 (recibido: 0)."

opcion_c_orrecta: 5
→ ❌ Error: "El índice de opción correcta debe ser 1, 2, 3 o 4 (recibido: 5)."

opcion_c_orrecta: "primero"
→ ❌ Error: "Opción correcta inválida 'primero'. Debe ser un número del 1 al 4."
```

### **Caso 6: Filas vacías (espacios en blanco)**
```
Fila 5: completamente vacía
→ ✅ Se ignora automáticamente (no genera error)
```

---

## 📝 Checklist para el Usuario

Antes de importar, verifica que tu Excel tenga:

- ✅ Todas las columnas requeridas (pregunta, opcion_1-4, opcion_c_orrecta, tiempo_segundos)
- ✅ Cada pregunta tiene texto (no está vacía)
- ✅ Cada pregunta tiene al menos 2 opciones con texto
- ✅ El número de opción correcta (1-4) apunta a una opción con texto
- ✅ El tiempo está entre 10 y 100 segundos
- ✅ Las URLs de imágenes empiezan con http:// o https:// (si las usas)

---

## 🎉 Beneficios

✅ **Errores claros y específicos** - Sabes exactamente qué fila y qué columna tiene el problema
✅ **Validación exhaustiva** - No se importan datos inconsistentes
✅ **Múltiples errores a la vez** - Ves todos los problemas, no solo el primero
✅ **Mensajes amigables** - Explican qué está mal y cómo arreglarlo
✅ **No pierde tiempo** - Detecta errores antes de guardar en BD

---

## 🚀 Cómo Probar

1. **Crea un Excel con errores intencionales:**
   ```
   - Deja una pregunta vacía
   - Pon tiempo = 5 (menor que 10)
   - Marca opcion_c_orrecta = 3 pero deja opcion_3 vacía
   ```

2. **Intenta importar**
   - Deberías ver una lista con todos los errores

3. **Corrige los errores y vuelve a importar**
   - Ahora debería funcionar correctamente

---

## 📌 Notas Técnicas

- Las validaciones se ejecutan **antes** de cargar en memoria
- Si hay **un solo error**, se detiene la importación completa
- Los errores se acumulan y se muestran **todos juntos**
- Las filas con errores se **omiten** (no detienen el resto)
- Si **todas las filas** tienen errores, se rechaza el archivo completo

---

🎊 **¡Sistema de validación robusto implementado!**
