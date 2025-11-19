# Correcciones Necesarias en doc_apis.yaml

## Resumen de Formatos de Respuesta en routes_api.py

### APIs con formato `{code, data, message}`:
- Partidas (todas)
- Skins (todas)
- Categorías (todas)
- Inventario (todas)
- Participantes (todas)
- Respuestas (todas)

### APIs con formato `{data: ...}`:
- api_obtener_usuarios → `{data: [usuarios]}`
- api_obtener_usuario_por_id → `{data: usuario}`
- api_obtener_cuestionarios → `{data: [cuestionarios]}`
- api_obtener_cuestionario_por_id → `{data: cuestionario}`
- api_obtener_preguntas → `{data: [preguntas]}`
- api_obtener_pregunta_por_id → `{data: pregunta}`
- api_obtener_opciones → `{data: [opciones]}`
- api_obtener_opcion_por_id → `{data: opcion}`

### APIs con formato `{mensaje: ...}`:
- api_registar_cuestionario → `{mensaje: "Cuestionario creado con éxito"}` (201)
- api_actualizar_cuestionario → `{mensaje: "Cuestionario actualizado con éxito"}` (201)
- api_registrar_pregunta → `{mensaje: "Pregunta creada con éxito"}` (201)
- api_actualizar_pregunta → `{mensaje: "Pregunta actualizada"}` (200)
- api_eliminar_pregunta → `{mensaje: "Pregunta eliminada logicamente"}` (200)
- api_registar_opcion → `{mensaje: "Opción creada con éxito"}` (201)
- api_actualizar_opcion → `{mensaje: "Opción actualizada"}` (200)
- api_eliminar_opcion → `{mensaje: "Opción eliminada"}` (200)

### APIs con formato `{ok, mensaje}` o `{ok, id_usuario, vigente}`:
- api_registrar_usuario → `{ok: true, mensaje: "..."}` (201) o `{error: "...", campo: "..."}` (409)
- api_actualizar_usuario → retorna el usuario completo (200)
- api_eliminar_usuario → `{ok: true, id_usuario: X, vigente: false}` (200)

### APIs con formato `{error: ...}`:
- Todos los errores devuelven `{error: "mensaje de error"}`

## Patrón de Respuestas Correcto

### Para APIs con code/data/message (Partidas, Skins, Categorías, Inventario, Participantes, Respuestas):
```yaml
'200':
  description: Operación exitosa
  content:
    application/json:
      schema:
        type: object
        properties:
          code:
            type: integer
            example: 1
          data:
            # Según el caso: objeto, array, o vacío
          message:
            type: string
            example: "Operación exitosa"
'400'/'404':
  description: Error
  content:
    application/json:
      schema:
        type: object
        properties:
          code:
            type: integer
            example: 0
          data:
            type: object
            example: {}
          message:
            type: string
            example: "Error description"
```

### Para APIs con {data: ...}:
```yaml
'200':
  description: Datos obtenidos correctamente
  content:
    application/json:
      schema:
        type: object
        properties:
          data:
            # Tipo según endpoint
```

### Para APIs con {mensaje: ...}:
```yaml
'200'/'201':
  description: Operación exitosa
  content:
    application/json:
      schema:
        type: object
        properties:
          mensaje:
            type: string
            example: "Operación exitosa"
```

### Para Errores Generales:
```yaml
'400'/'404'/'500':
  description: Error
  content:
    application/json:
      schema:
        type: object
        properties:
          error:
            type: string
            example: "Mensaje de error"
```

## Acciones Requeridas

1. ✅ Corregir api_obtener_usuarios y api_obtener_usuario_por_id (HECHO)
2. ⚠️ Corregir api_actualizar_usuario - debe retornar el usuario completo, no {ok, usuario}
3. ⚠️ Verificar api_eliminar_usuario tiene el formato correcto
4. ⚠️ Corregir todas las APIs de cuestionarios para usar {mensaje} en lugar de schemas complejos
5. ⚠️ Corregir todas las APIs de preguntas para usar {data} y {mensaje}
6. ⚠️ Corregir todas las APIs de opciones para usar {data} y {mensaje}
7. ⚠️ Las APIs de Partidas, Skins, Categorías, Inventario, Participantes y Respuestas ya usan el formato correcto {code, data, message}

## RequestBody Corrections

### api_registrar_pregunta necesita:
```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        required:
          - id_cuestionario
          - pregunta
          - num_pregunta
          - puntaje_base
        properties:
          id_cuestionario:
            type: integer
          pregunta:
            type: string
          num_pregunta:
            type: integer
          puntaje_base:
            type: integer
          tiempo:
            type: integer
            minimum: 10
            maximum: 100
            default: 15
          adjunto:
            type: string
            nullable: true
```

