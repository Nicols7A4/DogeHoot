# 🐛 Bugs Encontrados y Corregidos - DogeHoot

## Fecha: 3 de Noviembre, 2025

---

## ✅ BUGS CORREGIDOS

### 🔴 BUG CRÍTICO #1: No se valida que el cuestionario existe y está publicado
**Ubicación**: `controlador_partidas.py` - función `crear_partida()`

**Problema**: 
- Se podía crear una partida con un `id_cuestionario` inexistente
- Se podía crear una partida con un cuestionario no publicado (vigente=0)
- Esto causaría errores al intentar iniciar el juego

**Solución Implementada**:
```python
# Validar que el cuestionario existe y está publicado
cursor.execute("""
    SELECT id_cuestionario, vigente 
    FROM CUESTIONARIO 
    WHERE id_cuestionario = %s
""", (id_cuestionario,))
cuestionario = cursor.fetchone()

if not cuestionario:
    return False, "El cuestionario seleccionado no existe."

if cuestionario[1] != 1:  # vigente != 1
    return False, "El cuestionario no está publicado. Publícalo antes de crear una partida."
```

**Archivo modificado**: `/mysite/controladores/controlador_partidas.py`

---

### 🔴 BUG CRÍTICO #2: Cuestionario sin preguntas causa crash
**Ubicación**: `game_events.py` - evento `@socketio.on('iniciar_juego')`

**Problema**:
- Si un cuestionario no tiene preguntas, el juego se iniciaba igual
- Al intentar enviar la primera pregunta, causaba un crash por acceso a índice inexistente
- `partida['preguntas_data']` podría estar vacío

**Solución Implementada**:
```python
# Validación antes de iniciar
if not partida.get('preguntas_data') or len(partida['preguntas_data']) == 0:
    socketio.emit('error_juego', {
        'mensaje': 'Este cuestionario no tiene preguntas. No se puede iniciar el juego.'
    }, room=pin, namespace='/')
    return
```

**Archivo modificado**: `/mysite/game_events.py`

---

### 🟡 BUG MEDIO #3: id_usuario_anfitrion podía ser NULL
**Ubicación**: `controlador_partidas.py` - función `crear_partida()`

**Problema**:
- El parámetro `id_usuario_anfitrion=None` permitía crear partidas sin anfitrión
- Esto causaba problemas al mostrar "Mis Partidas"
- Partidas huérfanas sin dueño

**Solución Implementada**:
```python
# Validar que id_usuario_anfitrion no sea None
if id_usuario_anfitrion is None:
    return False, "Error: se requiere un usuario anfitrión para crear la partida."
```

**Archivo modificado**: `/mysite/controladores/controlador_partidas.py`

---

### 🟡 BUG MEDIO #4: Usuario puede unirse dos veces con diferentes sesiones
**Ubicación**: `game_events.py` - evento `@socketio.on('unirse_como_jugador')`

**Problema**:
- Solo se validaba el `nombre_usuario`, no el `id_usuario`
- Un usuario podía abrir dos navegadores y unirse dos veces
- Esto causaba duplicación de puntos y comportamiento inesperado

**Solución Implementada**:
```python
# Validar si el id_usuario ya existe en la partida
if id_usuario:  # Solo validar si el usuario está logueado
    for participante_nombre, participante_data in partida['participantes'].items():
        if participante_data.get('id_usuario') == id_usuario:
            # El usuario ya está en la partida
            socketio.emit('ya_en_partida', {
                'mensaje': 'Ya estás en esta partida.',
                'nombre': participante_nombre
            }, room=request.sid)
            return
```

**Archivo modificado**: `/mysite/game_events.py`

---

## ⚠️ BUGS IDENTIFICADOS (No críticos, considerar para futuro)

### 🟢 BUG MENOR #5: No hay manejo de desconexión del anfitrión
**Ubicación**: `game_events.py`

**Problema**:
- Si el anfitrión cierra el navegador durante el juego, no hay evento `@socketio.on('disconnect')`
- La partida queda en estado indefinido
- Los jugadores quedan esperando sin saber qué pasó

**Recomendación**:
```python
@socketio.on('disconnect')
def al_desconectar():
    # Verificar si el usuario desconectado era anfitrión
    # Si es anfitrión, notificar a los jugadores o finalizar automáticamente
    pass
```

---

### 🟢 BUG MENOR #6: Partidas huérfanas al reiniciar servidor
**Ubicación**: Sistema en general

**Problema**:
- `partidas_en_juego = {}` se pierde al reiniciar el servidor
- Las partidas en BD siguen con estado 'E' o 'J'
- No hay sincronización entre memoria y BD

**Recomendación**:
- Al iniciar el servidor, leer partidas activas de BD y cargarlas en memoria
- O marcar automáticamente como finalizadas las partidas antiguas
- Agregar un cron job o tarea programada para limpiar partidas abandonadas

---

### 🟢 BUG MENOR #7: Finalizar partida dos veces no está validado
**Ubicación**: `controlador_partidas.py` - función `finalizar_partida()`

**Problema**:
- No valida si `estado == 'F'` antes de actualizar
- Aunque no causa error, es redundante

**Recomendación**:
```python
# Verificar estado antes de finalizar
cursor.execute("SELECT estado FROM PARTIDA WHERE id_partida = %s", (id_partida,))
row = cursor.fetchone()
if row and row[0] == 'F':
    return  # Ya está finalizada
```

---

## 📊 RESUMEN

| Tipo | Cantidad | Estado |
|------|----------|--------|
| 🔴 Críticos Corregidos | 2 | ✅ FIXED |
| 🟡 Medios Corregidos | 2 | ✅ FIXED |
| 🟢 Menores Identificados | 3 | ⏳ PENDIENTE |
| **TOTAL** | **7** | **4/7 Corregidos** |

---

## 🧪 CASOS DE PRUEBA RECOMENDADOS

### Test 1: Cuestionario inexistente
1. Intentar crear partida con `id_cuestionario = 99999`
2. **Esperado**: Error "El cuestionario seleccionado no existe."

### Test 2: Cuestionario no publicado
1. Crear cuestionario con `vigente=0`
2. Intentar crear partida
3. **Esperado**: Error "El cuestionario no está publicado..."

### Test 3: Cuestionario sin preguntas
1. Crear cuestionario vacío (0 preguntas)
2. Crear partida exitosamente
3. Intentar iniciar juego
4. **Esperado**: Error "Este cuestionario no tiene preguntas..."

### Test 4: Usuario duplicado
1. Usuario A se une a partida desde Chrome
2. Usuario A intenta unirse desde Firefox (mismo id_usuario)
3. **Esperado**: Mensaje "Ya estás en esta partida."

### Test 5: Partida finalizada
1. Completar una partida hasta el final
2. Intentar unirse con el PIN
3. **Esperado**: Error "Esta partida ya ha finalizado. No puedes unirte."

---

## 🔧 ARCHIVOS MODIFICADOS

1. `/mysite/controladores/controlador_partidas.py`
   - Agregadas validaciones en `crear_partida()`
   
2. `/mysite/game_events.py`
   - Agregada validación en `al_iniciar_juego()`
   - Agregada validación en `al_unirse_jugador()`

---

## 📝 NOTAS TÉCNICAS

- Todos los cambios son **backward compatible**
- No se requieren migraciones de BD adicionales
- Los mensajes de error son claros y en español
- Se utilizan eventos de Socket.IO para comunicar errores en tiempo real
- Las validaciones siguen el principio de "fail fast" (fallar rápido)

---

**Última actualización**: 3 de Noviembre, 2025
**Responsable**: AI Assistant
**Revisión**: Pendiente por usuario
