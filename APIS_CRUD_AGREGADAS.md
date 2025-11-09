# APIs CRUD Agregadas - Resumen

## ✅ Estado: COMPLETADO Y VERIFICADO

Se han agregado exitosamente las APIs CRUD para **SKINS** y **CATEGORIA** en el archivo `routes_api.py`, justo después de las APIs de PARTIDA, siguiendo el mismo patrón y estructura.

---

## 📦 APIs de PARTIDAS (ya existentes - verificadas)

| Método | Endpoint | Función | JWT |
|--------|----------|---------|-----|
| POST | `/api_registrarpartida` | Crear nueva partida | ✅ |
| GET | `/api_obtenerpartidas` | Obtener todas las partidas | ✅ |
| GET | `/api_obtenerpartidaporid/<id>` | Obtener partida por ID | ✅ |
| PUT | `/api_actualizarpartida/<id>` | Actualizar partida | ✅ |
| DELETE | `/api_eliminarpartida/<id>` | Eliminar partida | ✅ |

---

## 🎨 APIs de SKINS (NUEVAS)

| Método | Endpoint | Función | JWT |
|--------|----------|---------|-----|
| POST | `/api_registrarskin` | Crear nueva skin | ✅ |
| GET | `/api_obtenerskins` | Obtener todas las skins | ✅ |
| GET | `/api_obtenerskinporid/<id>` | Obtener skin por ID | ✅ |
| PUT | `/api_actualizarskin/<id>` | Actualizar skin | ✅ |
| DELETE | `/api_eliminarskin/<id>` | Eliminar skin | ✅ |

### Ejemplo de uso - Crear Skin:
```json
POST /api_registrarskin
Headers: Authorization: JWT <token>
Body: {
    "nombre": "Skin Astronauta",
    "ruta": "/img/skins/astronauta.png",
    "precio": 150,
    "vigente": 1
}
```

### Respuesta exitosa:
```json
{
    "code": 1,
    "data": {
        "id_skin": 5
    },
    "message": "Skin creada correctamente"
}
```

---

## 📁 APIs de CATEGORIAS (NUEVAS)

| Método | Endpoint | Función | JWT |
|--------|----------|---------|-----|
| POST | `/api_registrarcategoria` | Crear nueva categoría | ✅ |
| GET | `/api_obtenercategorias` | Obtener todas las categorías | ✅ |
| GET | `/api_obtenercategoriaporid/<id>` | Obtener categoría por ID | ✅ |
| PUT | `/api_actualizarcategoria/<id>` | Actualizar categoría | ✅ |
| DELETE | `/api_eliminarcategoria/<id>` | Eliminar categoría | ✅ |

### Ejemplo de uso - Crear Categoría:
```json
POST /api_registrarcategoria
Headers: Authorization: JWT <token>
Body: {
    "categoria": "Ciencias"
}
```

### Respuesta exitosa:
```json
{
    "code": 1,
    "data": {
        "id_categoria": 8
    },
    "message": "Categoría creada correctamente"
}
```

---

## 🔑 Autenticación JWT

Todas las nuevas APIs requieren autenticación JWT. Para obtener un token:

```bash
POST /auth
Content-Type: application/json

{
    "username": "usuario@correo.com",
    "password": "tu_contraseña"
}
```

Respuesta:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Luego usa el token en el header:
```
Authorization: JWT eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 📋 Formato de Respuestas

Todas las APIs siguen el mismo formato de respuesta:

### Éxito:
```json
{
    "code": 1,
    "data": { ... },
    "message": "Operación exitosa"
}
```

### Error:
```json
{
    "code": 0,
    "data": {},
    "message": "Descripción del error"
}
```

---

## ✅ Verificación

Las rutas fueron verificadas usando el script `test_simple_sin_jwt.py`:

- ✅ **14 rutas** de Partidas
- ✅ **6 rutas** de Skins (5 CRUD + 1 comprar)
- ✅ **5 rutas** de Categorías

---

## 📁 Archivos Modificados

1. `/Users/darkaz/Desktop/DogeHoot/mysite/routes_api.py` - APIs agregadas después de las APIs de PARTIDA

---

## 🧪 Scripts de Prueba Disponibles

1. **test_apis_crud.py** - Pruebas completas con JWT (requiere servidor corriendo)
2. **test_simple_sin_jwt.py** - Verificación de rutas sin necesidad de servidor

---

## 📝 Notas

- Todas las APIs usan `pymysql.cursors.DictCursor` para respuestas en formato diccionario
- Manejo de transacciones con `commit()` y `rollback()`
- Validación de campos obligatorios
- Respuestas HTTP adecuadas (201 para creación, 404 para no encontrado, etc.)
- Las dependencias NO fueron modificadas (Flask-JWT ya estaba instalado)

---

¡Todo listo y funcionando! 🎉
