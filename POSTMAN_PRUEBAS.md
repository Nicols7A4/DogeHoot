# APIs CRUD - Guía de Pruebas en Postman

## 🔑 Paso 0: Obtener Token JWT

**Endpoint:** `POST http://localhost:5001/auth`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "username": "a@a.com",
    "password": "123"
}
```

**💡 Credenciales alternativas disponibles:**
```json
{
    "username": "adolfopongo1705@gmail.com",
    "password": "123"
}
```

**Respuesta esperada:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**⚠️ IMPORTANTE:** Copia el `access_token` y úsalo en todas las siguientes peticiones en el header `Authorization: JWT {token}`

---

## 🎨 SKINS - 5 Operaciones

### 1. Crear Skin

**Endpoint:** `POST http://localhost:5001/api_registrarskin`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "ruta": "img/skins/skin_prueba.png",
    "tipo": "marco",
    "precio": 150,
    "vigente": 1
}
```

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {
        "id_skin": 123
    },
    "message": "Skin creada correctamente"
}
```

---

### 2. Obtener Todas las Skins

**Endpoint:** `GET http://localhost:5001/api_obtenerskins`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": [
        {
            "id_skin": 123,
            "ruta": "img/skins/skin_prueba.png",
            "tipo": "marco",
            "precio": 150,
            "vigente": 1
        }
    ],
    "message": "Skins obtenidas correctamente"
}
```

---

### 3. Obtener Skin por ID

**Endpoint:** `GET http://localhost:5001/api_obtenerskinporid/123`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**⚠️ Nota:** Reemplaza `123` con el ID de la skin creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {
        "id_skin": 123,
        "ruta": "img/skins/skin_prueba.png",
        "tipo": "marco",
        "precio": 150,
        "vigente": 1
    },
    "message": "Skin obtenida correctamente"
}
```

---

### 4. Actualizar Skin

**Endpoint:** `PUT http://localhost:5001/api_actualizarskin/123`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "tipo": "fondo",
    "precio": 200
}
```

**⚠️ Nota:** Reemplaza `123` con el ID de la skin creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {},
    "message": "Skin actualizada correctamente"
}
```

---

### 5. Eliminar Skin

**Endpoint:** `DELETE http://localhost:5001/api_eliminarskin/123`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**⚠️ Nota:** Reemplaza `123` con el ID de la skin creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {},
    "message": "Skin eliminada correctamente"
}
```

---

## 📁 CATEGORIAS - 5 Operaciones

### 6. Crear Categoría

**Endpoint:** `POST http://localhost:5001/api_registrarcategoria`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "categoria": "Categoría de Prueba"
}
```

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {
        "id_categoria": 456
    },
    "message": "Categoría creada correctamente"
}
```

---

### 7. Obtener Todas las Categorías

**Endpoint:** `GET http://localhost:5001/api_obtenercategorias`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": [
        {
            "id_categoria": 456,
            "categoria": "Categoría de Prueba",
            "descripcion": null
        }
    ],
    "message": "Categorías obtenidas correctamente"
}
```

---

### 8. Obtener Categoría por ID

**Endpoint:** `GET http://localhost:5001/api_obtenercategoriaporid/456`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**⚠️ Nota:** Reemplaza `456` con el ID de la categoría creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {
        "id_categoria": 456,
        "categoria": "Categoría de Prueba",
        "descripcion": null
    },
    "message": "Categoría obtenida correctamente"
}
```

---

### 9. Actualizar Categoría

**Endpoint:** `PUT http://localhost:5001/api_actualizarcategoria/456`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "categoria": "Categoría Actualizada"
}
```

**⚠️ Nota:** Reemplaza `456` con el ID de la categoría creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {},
    "message": "Categoría actualizada correctamente"
}
```

---

### 10. Eliminar Categoría

**Endpoint:** `DELETE http://localhost:5001/api_eliminarcategoria/456`

**Headers:**
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

**⚠️ Nota:** Reemplaza `456` con el ID de la categoría creada

**Respuesta esperada:**
```json
{
    "code": 1,
    "data": {},
    "message": "Categoría eliminada correctamente"
}
```

---

## 📝 Notas Importantes

### Estructura de la tabla SKINS:
- `id_skin` (int, PK, auto_increment)
- `ruta` (text, obligatorio) - Ruta de la imagen
- `tipo` (enum: 'marco' o 'fondo', default: 'marco')
- `precio` (int, default: 100)
- `vigente` (tinyint, 0 o 1)

### Estructura de la tabla CATEGORIA:
- `id_categoria` (int, PK, auto_increment)
- `categoria` (varchar, obligatorio) - Nombre de la categoría
- `descripcion` (text, opcional)

### Formato de Respuestas:
Todas las APIs siguen este formato:

**Éxito (code: 1):**
```json
{
    "code": 1,
    "data": { ... },
    "message": "Mensaje descriptivo"
}
```

**Error (code: 0):**
```json
{
    "code": 0,
    "data": {},
    "message": "Descripción del error"
}
```

### Códigos de Estado HTTP:
- `200` - OK (operación exitosa)
- `201` - Created (recurso creado)
- `400` - Bad Request (datos inválidos)
- `401` - Unauthorized (sin token o token inválido)
- `404` - Not Found (recurso no encontrado)
- `500` - Internal Server Error (error del servidor)

---

## 🚀 Flujo Recomendado para Probar en Postman

1. **Obtener Token JWT** (Paso 0)
2. **Crear Skin** (Operación 1) - Guarda el `id_skin` de la respuesta
3. **Obtener Todas las Skins** (Operación 2)
4. **Obtener Skin por ID** (Operación 3) - Usa el `id_skin` guardado
5. **Actualizar Skin** (Operación 4) - Usa el `id_skin` guardado
6. **Crear Categoría** (Operación 6) - Guarda el `id_categoria` de la respuesta
7. **Obtener Todas las Categorías** (Operación 7)
8. **Obtener Categoría por ID** (Operación 8) - Usa el `id_categoria` guardado
9. **Actualizar Categoría** (Operación 9) - Usa el `id_categoria` guardado
10. **Eliminar Skin** (Operación 5) - Limpieza
11. **Eliminar Categoría** (Operación 10) - Limpieza

---

## 💡 Tips para Postman

1. **Crear una Colección:** Agrupa todas estas peticiones en una colección llamada "DogeHoot CRUD APIs"

2. **Variables de Entorno:** Crea variables para reutilizar valores:
   - `base_url` = `http://localhost:5001`
   - `jwt_token` = (token obtenido en Paso 0)
   - `skin_id` = (ID de skin creada)
   - `categoria_id` = (ID de categoría creada)

3. **Scripts de Postman:** Puedes automatizar guardar el token en una variable:
   ```javascript
   // En el tab "Tests" de la petición de auth:
   pm.environment.set("jwt_token", pm.response.json().access_token);
   ```

4. **Uso de Variables:** En las URLs y headers, usa `{{variable_name}}`:
   - URL: `{{base_url}}/api_registrarskin`
   - Header: `Authorization: JWT {{jwt_token}}`

---

✅ **¡Listo para copiar y pegar en Postman!**
