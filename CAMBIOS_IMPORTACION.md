# 📋 Cambios en el Sistema de Importación de Preguntas

## ✅ Cambios Realizados

### 1. **Nuevo Formato de Plantilla Excel**

#### Formato Anterior (❌ OBSOLETO):
```
pregunta | opcion_correcta | opcion_incorrecta_1 | opcion_incorrecta_2 | opcion_incorrecta_3 | url_imagen
```

#### Nuevo Formato (✅ ACTUAL):
```
pregunta | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta | tiempo_segundos | url_imagen
```

**Diferencias clave:**
- ✅ Ahora todas las opciones están numeradas (opcion_1 a opcion_4)
- ✅ La columna `opcion_c_orrecta` contiene el **número** (1, 2, 3 o 4) de la opción correcta
- ✅ La columna `tiempo_segundos` es **obligatoria** y debe estar entre 10 y 100
- ✅ La columna `url_imagen` es **opcional**
- ✅ La respuesta correcta ya **NO** aparece siempre primera
- ✅ **NO SE GUARDA EN BD** automáticamente - solo carga en memoria

#### Ejemplo de datos:
```
| pregunta      | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta | tiempo_segundos | url_imagen |
|---------------|----------|----------|----------|----------|------------------|-----------------|------------|
| Que dia es hoy?| Martes   | Viernes  | Jueves   | Lunes    | 3                | 15              |            |
| 2 + 2         | 4        | 5        | 0        | 1        | 1                | 20              |            |
```

En el primer ejemplo, la respuesta correcta es "Jueves" (opcion_3 → índice 3)
En el segundo ejemplo, la respuesta correcta es "4" (opcion_1 → índice 1)

---

### 2. **Backend Actualizado** (`mysite/controladores/importarExcel.py`)

#### ⚠️ CAMBIO CRÍTICO: Ya NO guarda en BD

**Antes:**
```python
# Guardaba directamente en BD con INSERT
cursor.execute("INSERT INTO PREGUNTAS ...")
connection.commit()
# Luego recuperaba del servidor
cuestionario_actualizado = cc.obtener_completo_por_id(id_cuestionario)
```

**Ahora:**
```python
# Solo formatea JSON sin tocar la BD
pregunta_obj = {
    'num_pregunta': len(preguntas_formateadas) + 1,
    'pregunta': texto_pregunta,
    'puntaje_base': 1000,
    'tiempo': tiempo_segundos,  # Obtenido del Excel
    'adjunto': url_imagen,
    'opciones': opciones
}
preguntas_formateadas.append(pregunta_obj)
# Devuelve JSON sin guardar
return jsonify({'preguntas_actualizadas': preguntas_formateadas})
```

#### Validaciones añadidas:
- ✅ Valida que `opcion_c_orrecta` contenga un número entre 1 y 4
- ✅ Valida que `tiempo_segundos` esté entre 10 y 100 (obligatorio)
- ✅ Verifica que la opción marcada como correcta no esté vacía
- ✅ Requiere mínimo 2 opciones (1 correcta + 1 incorrecta)
- ✅ Soporta URLs de imágenes opcionales
- ✅ **NO persiste nada en BD** - solo formatea y devuelve JSON

---

### 3. **Frontend Actualizado** (`mysite/templates/mantenimiento_cuestionario.html`)

#### Cambios en el comportamiento de importación:

**Antes:**
```javascript
// Añadía preguntas a las existentes
cuestionarioData.preguntas = result.preguntas_actualizadas;
// ❌ Sincronizaba originalCuestionarioData (guardaba automáticamente)
originalCuestionarioData.preguntas = JSON.parse(JSON.stringify(result.preguntas_actualizadas));
```

**Ahora:**
```javascript
// ✅ REEMPLAZA todas las preguntas existentes
cuestionarioData.preguntas = preguntasNormalizadas;
// ✅ NO sincroniza con original (marca cambios pendientes)
// originalCuestionarioData.preguntas = ... (comentado)
// ✅ Marca que hay cambios sin guardar
onAnyChange();
```

#### Flujo actualizado:
1. Usuario importa Excel → Preguntas se cargan en **memoria**
2. Sistema **reemplaza** preguntas existentes (no añade)
3. Sistema **no guarda automáticamente** en BD
4. Botón "Guardar cambios" se **habilita**
5. Usuario puede **revisar/editar** antes de guardar
6. Usuario presiona "Guardar cambios" → Se persiste en BD

---

### 4. **Nueva Plantilla Excel Generada**

**Ubicación:** `mysite/static/cuestionario_plantilla.xlsx`

**Características:**
- ✅ Encabezados con fondo azul y texto blanco
- ✅ Incluye 2 ejemplos de preguntas
- ✅ Ancho de columnas auto-ajustado
- ✅ Formato correcto: `pregunta | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta | url_imagen`

**Para regenerar la plantilla:**
```bash
python generar_plantilla.py
```

---

### 5. **Mensaje del Modal Actualizado**

**Antes:**
> "Sube un archivo .xlsx. Las preguntas se añadirán a este cuestionario."

**Ahora:**
> "Sube un archivo .xlsx con el formato: pregunta | opcion_1 | opcion_2 | opcion_3 | opcion_4 | opcion_c_orrecta (1-4) | url_imagen. Las preguntas **reemplazarán** las existentes en memoria."

---

## 🎯 Ventajas del Nuevo Sistema

1. ✅ **Mayor flexibilidad**: La respuesta correcta puede estar en cualquier posición (no siempre primera)
2. ✅ **Más intuitivo**: Número (1-4) en lugar de duplicar el texto de la respuesta
3. ✅ **Control del usuario**: NO guarda automáticamente en BD - permite revisión antes de persistir
4. ✅ **Reemplazo completo**: Evita acumulación de preguntas duplicadas
5. ✅ **Validación robusta**: Detecta errores de formato antes de procesar
6. ✅ **Tiempo personalizable**: Cada pregunta puede tener su propio tiempo (10-100 seg)
7. ✅ **Sin efectos secundarios**: La BD NO se toca hasta que el usuario presione "Guardar cambios"

---

## 📝 Notas Importantes

- ⚠️ **Compatibilidad**: Archivos Excel con el formato antiguo **NO funcionarán**
- ⚠️ **Sin persistencia automática**: Al importar se cargan preguntas en **memoria únicamente** - NO se guardan en BD hasta presionar "Guardar cambios"
- ⚠️ **Reemplazo total**: Las preguntas importadas **reemplazan completamente** las que estaban en memoria
- ⚠️ **Validación**: El sistema valida que el índice de opción correcta apunte a una opción no vacía
- ⚠️ **tiempo_segundos**: Es **obligatorio** y debe estar entre 10 y 100 segundos
- ℹ️ **url_imagen**: Es **opcional**, puede dejarse vacía

---

## 🧪 Cómo Probar

1. Descargar la plantilla desde el modal "Importar Preguntas"
2. Llenar con preguntas de prueba:
   - Asegurar que `opcion_c_orrecta` tenga valores 1-4
   - Asegurar que `tiempo_segundos` tenga valores entre 10-100
3. Importar el archivo
4. ✅ Verificar que las preguntas se carguen en memoria (reemplazando las anteriores)
5. ✅ Verificar que el botón "Guardar cambios" esté habilitado
6. ✅ Verificar que la BD **NO** se haya modificado (las preguntas viejas siguen ahí)
7. Presionar "Guardar cambios"
8. ✅ Verificar persistencia en BD (ahora sí deben guardarse)

**Archivo de prueba:** Se ha creado `test_preguntas.xlsx` con 3 preguntas de ejemplo.

---

## 🐛 Posibles Errores y Soluciones

### Error: "El archivo Excel debe tener las columnas 'pregunta', 'opcion_c_orrecta' y 'tiempo_segundos'"
**Causa:** Formato de plantilla antiguo o columnas faltantes
**Solución:** Descargar la nueva plantilla desde el modal

### Error: "El índice de opción correcta debe ser entre 1 y 4"
**Causa:** Valor inválido en columna `opcion_c_orrecta`
**Solución:** Asegurar que contenga solo números del 1 al 4

### Error: "El tiempo debe estar entre 10 y 100 segundos"
**Causa:** Valor de `tiempo_segundos` fuera del rango permitido
**Solución:** Usar valores entre 10 y 100 (ejemplo: 15, 20, 30)

### Error: "La opción correcta (índice X) está vacía"
**Causa:** La opción marcada como correcta no tiene texto
**Solución:** Verificar que la opción señalada tenga contenido

### Error: "Se necesitan al menos 2 opciones"
**Causa:** Menos de 2 opciones con contenido
**Solución:** Completar al menos 2 opciones (1 correcta + 1 incorrecta)

### Problema: "Las preguntas viejas siguen apareciendo después de importar"
**Causa:** El backend antiguo guardaba en BD automáticamente
**Solución:** ✅ **YA RESUELTO** - El nuevo código NO guarda en BD, solo carga en memoria

---

**Fecha de actualización:** 31 de octubre de 2025
**Archivos modificados:**
- `mysite/controladores/importarExcel.py`
- `mysite/templates/mantenimiento_cuestionario.html`
- `mysite/static/cuestionario_plantilla.xlsx`
- `generar_plantilla.py` (nuevo)
