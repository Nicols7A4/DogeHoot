# 🔍 DEBUG: Mensaje "INCORRECTO" no aparece

## 📝 Logs Agregados

He agregado logs detallados en toda la cadena de ejecución para diagnosticar el problema.

### 🔴 Backend (Terminal)

#### 1. Cuando se recibe una respuesta (`al_recibir_respuesta`):
```
🎯 [RESPUESTA] Usuario 'Juan' respondió. Correcta: False, Puntos: 0
✅ [INDIVIDUAL] 'Juan' marcado como respondido. Puntaje: 0
```

#### 2. Cuando se calculan los resultados (`mostrar_resultados_pregunta`):
```
🔍 [BACKEND] Jugador 'Juan': puntaje=0, puntos_ganados=0, respondio=True
```

#### 3. Antes de emitir los resultados:
```
📤 [EMIT] Enviando resultados: {'texto_opcion_correcta': 'París', 'ranking': [{'nombre': 'Juan', 'puntaje': 0, 'puntos_ganados': 0, 'respondio': True}]}
```

### 🔵 Frontend (Consola del Navegador - F12)

#### 1. Cuando se recibe el evento:
```
📥 [EVENTO] mostrar_resultados recibido: {texto_opcion_correcta: 'París', ranking: [...]}
📊 [RANKING] Datos del ranking: [{nombre: 'Juan', puntaje: 0, puntos_ganados: 0, respondio: true}]
```

#### 2. Al buscar el jugador en el ranking:
```
🔍 [DEBUG] Buscando en ranking para: miNombre="Juan", miGrupo="null"
📋 [DEBUG] Ranking completo: [{nombre: 'Juan', puntaje: 0, puntos_ganados: 0, respondio: true}]
🎯 [DEBUG] miEntry encontrado: {nombre: 'Juan', puntaje: 0, puntos_ganados: 0, respondio: true}
```

#### 3. Valores extraídos:
```
🔍 [FRONTEND] Juan: puntaje=0, puntos_ganados=0, respondio=true
```

#### 4. Evaluación de condiciones:
```
🧪 [TEST] Evaluando condiciones: puntosGanados=0, miGrupoRespondio=true
❌ [CASO 2] Mostrando: INCORRECTO (respondio=true, puntos=0)
```

---

## 🧪 Pasos para Probar

### **Prueba 1: Respuesta Incorrecta en Modo Individual**

1. Inicia el servidor: `python .\mysite\main.py`
2. Crea una partida en **modo individual** (sin grupos)
3. Únete como jugador
4. Responde **INCORRECTAMENTE** (selecciona la opción incorrecta)
5. Espera a que termine el tiempo

**Logs Esperados en Terminal:**
```
🎯 [RESPUESTA] Usuario 'TuNombre' respondió. Correcta: False, Puntos: 0
✅ [INDIVIDUAL] 'TuNombre' marcado como respondido. Puntaje: 0
🔍 [BACKEND] Jugador 'TuNombre': puntaje=0, puntos_ganados=0, respondio=True
📤 [EMIT] Enviando resultados: {..., 'respondio': True}
```

**Logs Esperados en Navegador (F12 > Consola):**
```
🔍 [FRONTEND] TuNombre: puntaje=0, puntos_ganados=0, respondio=true
🧪 [TEST] Evaluando condiciones: puntosGanados=0, miGrupoRespondio=true
❌ [CASO 2] Mostrando: INCORRECTO (respondio=true, puntos=0)
```

**Resultado en Pantalla:**
- Debería ver: **"INCORRECTO"** en rojo

---

### **Prueba 2: Respuesta Incorrecta en Modo Grupal**

1. Crea una partida en **modo grupal** (2 grupos)
2. Únete con 2 usuarios en diferentes grupos
3. Solo 1 grupo responde **INCORRECTAMENTE**
4. Espera a que termine el tiempo

**Logs Esperados en Terminal:**
```
🎯 [RESPUESTA] Usuario 'Juan' respondió. Correcta: False, Puntos: 0
✅ [GRUPO] 'Grupo 1' marcado como respondido. Puntaje: 0
🔍 [BACKEND] Grupo 'Grupo 1': puntaje=0, puntos_ganados=0, respondio=True
🔍 [BACKEND] Grupo 'Grupo 2': puntaje=0, puntos_ganados=0, respondio=False
```

**Logs Esperados en Navegador (Grupo 1):**
```
❌ [CASO 2] Mostrando: INCORRECTO (respondio=true, puntos=0)
```

**Logs Esperados en Navegador (Grupo 2):**
```
⚪ [CASO 3] Mostrando: SIN RESPUESTA (respondio=false, puntos=0)
```

---

## 🔍 Posibles Problemas a Verificar

### ❌ **Problema 1: `respondio` llega como `undefined`**

Si en el navegador ves:
```
🔍 [FRONTEND] Juan: puntaje=0, puntos_ganados=0, respondio=undefined
```

**Causa:** El backend no está enviando la flag `respondio` en el ranking.

**Solución:** Verificar que en `game_events.py` líneas 364 y 395 se esté agregando `'respondio': ...` al diccionario.

---

### ❌ **Problema 2: `miEntry` es `null`**

Si en el navegador ves:
```
🎯 [DEBUG] miEntry encontrado: null
❌ [ERROR] No se encontró entrada en el ranking para este jugador/grupo
```

**Causa:** El nombre del jugador no coincide con el nombre en el ranking.

**Solución:** Verificar que `session.get('nombre_usuario')` coincida exactamente con el nombre en el backend.

---

### ❌ **Problema 3: `puntaje_anterior` no se resetea**

Si ves que `puntos_ganados` es siempre el puntaje total en lugar de los puntos de esta pregunta:

**Causa:** `puntaje_anterior` no se está inicializando correctamente.

**Solución:** Verificar líneas 223-231 de `game_events.py`.

---

### ❌ **Problema 4: JavaScript compara string vs boolean**

Si `respondio` llega como `"True"` (string) en lugar de `true` (boolean):

**Causa:** Python está convirtiendo el booleano a string.

**Solución:** Asegurarse de que Flask/SocketIO convierte correctamente los booleanos.

---

## 📋 Checklist de Verificación

Antes de probar, verifica:

- [ ] El servidor Flask está ejecutándose
- [ ] Has refrescado la página del navegador (Ctrl+F5)
- [ ] La consola del navegador está abierta (F12)
- [ ] El terminal del backend es visible para ver los logs
- [ ] Has hecho al menos UNA prueba respondiendo incorrectamente

---

## 📞 Información a Proporcionar

Si el problema persiste, copia y pega:

1. **Logs del Terminal (Backend)** desde que envías la respuesta hasta que se muestran los resultados
2. **Logs de la Consola del Navegador (F12)** completos
3. **Modo de juego:** Individual o Grupal
4. **Qué mensaje viste:** CORRECTO / SIN RESPUESTA / ninguno

---

**Fecha:** 1 de noviembre de 2025  
**Estado:** 🔍 DEBUGGING - Logs agregados
