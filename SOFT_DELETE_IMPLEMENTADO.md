# ✅ Implementación de Eliminación Lógica (Soft Delete)

## 🎯 Objetivo
Permitir que las preguntas y opciones se "eliminen" sin borrarlas físicamente de la base de datos, preservando así el historial de partidas y reportes.

---

## 📋 Cambios Realizados

### 1. **Base de Datos (SQL)**
Se agregó la columna `vigente` a dos tablas:

```sql
ALTER TABLE PREGUNTAS ADD COLUMN vigente TINYINT(1) NOT NULL DEFAULT 1;
ALTER TABLE OPCIONES ADD COLUMN vigente TINYINT(1) NOT NULL DEFAULT 1;
```

**¿Qué hace?**
- `vigente = 1`: La pregunta/opción está activa y se muestra normalmente
- `vigente = 0`: La pregunta/opción fue "eliminada" pero sigue en la BD para reportes

---

### 2. **Backend (cuestionarios.py)**

#### ✅ Cambios en `obtener_completo_por_id()`
**Líneas 129 y 134:**
```python
# ANTES:
sql_preguntas = "SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s ORDER BY num_pregunta ASC"
sql_opciones = "SELECT * FROM OPCIONES WHERE id_pregunta = %s"

# DESPUÉS:
sql_preguntas = "SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1 ORDER BY num_pregunta ASC"
sql_opciones = "SELECT * FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1"
```
**Efecto:** Solo se cargan preguntas y opciones vigentes en el editor.

---

#### ✅ Cambios en `guardar_o_actualizar_completo()`

**Línea 253 - Obtener IDs vigentes:**
```python
# ANTES:
cursor.execute("SELECT id_pregunta FROM PREGUNTAS WHERE id_cuestionario = %s", (id_cuestionario,))

# DESPUÉS:
cursor.execute("SELECT id_pregunta FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1", (id_cuestionario,))
```

**Línea 287 - Filtrar opciones vigentes:**
```python
# ANTES:
cursor.execute("SELECT id_opcion FROM OPCIONES WHERE id_pregunta = %s", (id_pregunta,))

# DESPUÉS:
cursor.execute("SELECT id_opcion FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1", (id_pregunta,))
```

**Líneas 308-311 - Soft delete de opciones:**
```python
# ANTES (hard delete):
cursor.execute("DELETE FROM OPCIONES WHERE id_opcion = %s", (id_opcion_eliminar,))

# DESPUÉS (soft delete):
cursor.execute("UPDATE OPCIONES SET vigente = 0 WHERE id_opcion = %s", (id_opcion_eliminar,))
```

**Líneas 320-325 - INSERT con vigente:**
```python
# ANTES:
INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo)
VALUES (%s, %s, %s, %s, %s)

# DESPUÉS:
INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
VALUES (%s, %s, %s, %s, %s, 1)
```

**Líneas 343-346 - INSERT opciones con vigente:**
```python
# ANTES:
INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto)
VALUES (%s, %s, %s, %s, %s)

# DESPUÉS:
INSERT INTO OPCIONES (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
VALUES (%s, %s, %s, %s, %s, 1)
```

**Líneas 351-355 - Soft delete de preguntas:**
```python
# ANTES (hard delete con protección):
cursor.execute("SELECT COUNT(*) as count FROM RESPUESTA_PARTICIPANTE WHERE id_pregunta = %s", (id_pregunta_eliminar,))
if result['count'] == 0:
    cursor.execute("DELETE FROM PREGUNTAS WHERE id_pregunta = %s", (id_pregunta_eliminar,))

# DESPUÉS (soft delete sin protección):
cursor.execute("UPDATE PREGUNTAS SET vigente = 0 WHERE id_pregunta = %s", (id_pregunta_eliminar,))
cursor.execute("UPDATE OPCIONES SET vigente = 0 WHERE id_pregunta = %s", (id_pregunta_eliminar,))
```

**Líneas 378-381 - Cuestionario nuevo con vigente:**
```python
# Las preguntas nuevas también se insertan con vigente = 1
INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
VALUES (%s, %s, %s, %s, %s, 1)
```

---

## 🔥 Beneficios

✅ **Las preguntas importadas ahora SÍ reemplazan las viejas** (se marcan como `vigente = 0`)
✅ **Los reportes siguen funcionando** porque las preguntas viejas NO se eliminan de la BD
✅ **El historial de partidas se preserva** (RESPUESTA_PARTICIPANTE sigue teniendo los IDs)
✅ **No se pierde información** - Todo queda archivado en la BD

---

## 🧪 Cómo Probar

### Paso 1: Ejecutar el SQL
```bash
# En MySQL/phpMyAdmin, ejecuta:
mysql -u tu_usuario -p tu_base_de_datos < agregar_vigente_preguntas_opciones.sql
```

### Paso 2: Reiniciar Flask
```bash
python mysite/main.py
```

### Paso 3: Probar Importación
1. Abre un cuestionario **con data histórica** (que tenga partidas jugadas)
2. Importa un archivo Excel con preguntas nuevas
3. Presiona "Guardar cambios"
4. ✅ Las preguntas viejas deben desaparecer
5. ✅ Las preguntas nuevas deben aparecer
6. ✅ Los reportes viejos deben seguir mostrando las preguntas originales

### Paso 4: Verificar en BD
```sql
-- Ver preguntas marcadas como no vigentes
SELECT id_pregunta, pregunta, vigente 
FROM PREGUNTAS 
WHERE vigente = 0;

-- Ver opciones marcadas como no vigentes
SELECT id_opcion, opcion, vigente 
FROM OPCIONES 
WHERE vigente = 0;
```

---

## 🛡️ Seguridad

- ✅ **No se pierden datos** - Todo se marca como no vigente, no se elimina
- ✅ **Integridad referencial** - Los reportes siguen vinculados a las preguntas originales
- ✅ **Reversible** - Si quieres "restaurar" una pregunta, solo haz `UPDATE PREGUNTAS SET vigente = 1 WHERE id_pregunta = X`

---

## 📝 Notas Finales

- Las preguntas con `vigente = 0` **NO aparecen** en el editor de mantenimiento
- Las preguntas con `vigente = 0` **SÍ aparecen** en los reportes de partidas (porque usas `pregunta_texto`)
- Puedes hacer limpieza periódica de preguntas viejas si quieres: `DELETE FROM PREGUNTAS WHERE vigente = 0 AND fecha < '2024-01-01'`

---

## 🎉 Resultado Final

**Antes:** ⚠️ Las preguntas con respuestas NO se podían eliminar/reemplazar

**Ahora:** ✅ Las preguntas se pueden reemplazar libremente, manteniendo el historial intacto

🚀 **¡Listo para producción!**
