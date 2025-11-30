# 📚 FLUJO DE MANTENIMIENTO DE CUESTIONARIOS - DogeHoot

## 📖 ÍNDICE
1. [Arquitectura General](#arquitectura-general)
2. [Flujo de Creación](#flujo-de-creación)
3. [Flujo de Edición](#flujo-de-edición)
4. [Flujo de Clonación](#flujo-de-clonación)
5. [Soft Delete y Vigencia](#soft-delete-y-vigencia)
6. [Endpoints API](#endpoints-api)
7. [Esquema de Base de Datos](#esquema-de-base-de-datos)

---

## 🏗️ ARQUITECTURA GENERAL

### **Componentes Principales**

```
┌─────────────────────┐
│   FRONTEND (HTML)   │
│  Jinja2 Templates   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ROUTES_WEB.PY     │ ← Rutas para páginas HTML
│  (Flask Routes)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ROUTES_API.PY     │ ← Endpoints REST con @jwt_required()
│  (REST API)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CONTROLADORES/     │
│  cuestionarios.py   │ ← Lógica de negocio
│  preguntas_opciones.py
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    BD.PY            │ ← Conexión a MySQL/TiDB
│  obtener_conexion() │
└─────────────────────┘
```

### **Tablas de Base de Datos**

```sql
CUESTIONARIO
├── id_cuestionario (PK)
├── titulo
├── descripcion
├── es_publico (BOOLEAN)
├── fecha_hora_creacion
├── id_usuario (FK → USUARIO)
├── id_categoria (FK → CATEGORIA)
├── id_cuestionario_original (FK → CUESTIONARIO, para clones)
└── vigente (TINYINT 0/1)

PREGUNTAS
├── id_pregunta (PK)
├── id_cuestionario (FK → CUESTIONARIO)
├── pregunta (TEXT)
├── num_pregunta (INT)
├── puntaje_base (INT)
├── tiempo (SMALLINT, segundos)
├── adjunto (VARCHAR, ruta imagen)
└── vigente (TINYINT 0/1)

OPCIONES
├── id_opcion (PK)
├── id_pregunta (FK → PREGUNTAS)
├── opcion (VARCHAR)
├── es_correcta_bool (TINYINT 0/1)
├── descripcion (TEXT)
├── adjunto (TEXT)
└── vigente (TINYINT 0/1)
```

---

## 🆕 FLUJO DE CREACIÓN

### **1. INICIO: Usuario accede a crear cuestionario**

```python
# routes_web.py - Línea 553
@app.route("/cuestionarios/nuevo")
@profesor_required  # ← Solo profesores
def cuestionarios_nuevo():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para crear un cuestionario.', 'warning')
        return redirect(url_for('auth_page'))

    categorias = ctrl_cat.obtener_todas()  # ← Carga categorías disponibles

    return render_template(
        'mantenimiento_cuestionario.html',
        nombre_usuario=session.get('nombre_usuario'),
        tipo_usuario=session['tipo_usuario'],
        cuestionario_data=None,  # ← None indica NUEVO cuestionario
        categorias=categorias,
        modo='nuevo'
    )
```

**¿Qué hace?**
- Verifica que el usuario sea **profesor** (`@profesor_required`)
- Carga las **categorías** desde la BD para el dropdown
- Renderiza el template con `cuestionario_data=None` (indica modo creación)

---

### **2. FRONTEND: Formulario de creación**

El usuario llena:
- **Título**: Nombre del cuestionario
- **Descripción**: Breve explicación
- **Categoría**: Selecciona de dropdown (Matemáticas, Historia, etc.)
- **Es Público**: Checkbox (¿otros profesores pueden verlo?)
- **Preguntas**: Array de objetos con:
  - Texto de pregunta
  - Tiempo (segundos)
  - Puntaje base
  - Adjunto (imagen en Base64)
  - Opciones (array):
    - Texto de opción
    - `es_correcta_bool` (true/false)

---

### **3. ENVÍO: Frontend hace POST a API**

```javascript
// mantenimiento_cuestionario.html (JavaScript)
const datosEnviar = {
    id_cuestionario: null,  // ← null para nuevo
    titulo: "Matemáticas Básicas",
    descripcion: "Cuestionario de sumas y restas",
    es_publico: true,
    id_usuario: 15,  // ← Del session
    id_categoria: 3,
    preguntas: [
        {
            pregunta: "¿Cuánto es 2+2?",
            num_pregunta: 1,
            puntaje_base: 100,
            tiempo: 15,
            adjunto: "data:image/png;base64,iVBOR...",  // ← Imagen opcional
            opciones: [
                { opcion: "3", es_correcta_bool: false },
                { opcion: "4", es_correcta_bool: true },
                { opcion: "5", es_correcta_bool: false }
            ]
        }
    ]
};

fetch('/api/cuestionarios/guardar-completo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datosEnviar)
});
```

---

### **4. BACKEND: Endpoint recibe datos**

```python
# routes_api.py - Línea 565
@app.route("/api/cuestionarios/guardar-completo", methods=['POST'])
def cuestionarios_guardar_completo():
    try:
        data = request.get_json()
        
        # Llama al controlador que hace la lógica pesada
        id_cuestionario = cc.guardar_cuestionario_completo(data)
        
        return jsonify({
            "ok": True,
            "id_cuestionario": id_cuestionario,
            "mensaje": "Cuestionario guardado exitosamente"
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
```

---

### **5. CONTROLADOR: Lógica de guardado**

```python
# controladores/cuestionarios.py - Línea 306
def guardar_cuestionario_completo(data):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            
            # ══════════════════════════════════════════
            # CASO 1: NUEVO CUESTIONARIO (id_cuestionario = None)
            # ══════════════════════════════════════════
            if not data.get('id_cuestionario'):
                
                # --- PASO A: Insertar cuestionario ---
                sql_insert = """
                    INSERT INTO CUESTIONARIO 
                    (titulo, descripcion, es_publico, fecha_hora_creacion, 
                     id_usuario, id_categoria, id_cuestionario_original, vigente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """
                cursor.execute(sql_insert, (
                    data['titulo'],
                    data['descripcion'],
                    data['es_publico'],
                    datetime.now(),
                    data['id_usuario'],
                    data['id_categoria'],
                    data.get('id_cuestionario_original')  # ← None si no es clon
                ))
                
                id_cuestionario = cursor.lastrowid  # ← ID del nuevo cuestionario
                
                # --- PASO B: Insertar preguntas ---
                for index, pregunta_data in enumerate(data.get('preguntas', [])):
                    sql_pregunta = """
                        INSERT INTO PREGUNTAS 
                        (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
                        VALUES (%s, %s, %s, %s, %s, 1)
                    """
                    cursor.execute(sql_pregunta, (
                        id_cuestionario,
                        pregunta_data['pregunta'],
                        index + 1,  # ← num_pregunta empieza en 1
                        pregunta_data['puntaje_base'],
                        pregunta_data['tiempo']
                    ))
                    
                    id_pregunta_nueva = cursor.lastrowid
                    
                    # --- PASO C: Guardar imagen si existe ---
                    ruta_img = _guardar_imagen_base64(
                        id_cuestionario, 
                        id_pregunta_nueva, 
                        pregunta_data.get('adjunto')
                    )
                    if ruta_img:
                        cursor.execute(
                            "UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s",
                            (ruta_img, id_pregunta_nueva)
                        )
                    
                    # --- PASO D: Insertar opciones ---
                    for opcion_data in pregunta_data.get('opciones', []):
                        sql_opcion = """
                            INSERT INTO OPCIONES 
                            (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                            VALUES (%s, %s, %s, %s, %s, 1)
                        """
                        cursor.execute(sql_opcion, (
                            id_pregunta_nueva,
                            opcion_data['opcion'],
                            opcion_data['es_correcta_bool'],
                            opcion_data.get('descripcion'),
                            opcion_data.get('adjunto')
                        ))
        
        conexion.commit()  # ← Confirmar transacción
        return id_cuestionario
        
    except Exception as e:
        conexion.rollback()  # ← Revertir si hay error
        raise e
    finally:
        conexion.close()
```

**Función auxiliar para guardar imágenes:**

```python
# controladores/cuestionarios.py - Línea 138
def _guardar_imagen_base64(id_cuestionario, id_pregunta, adjunto_base64):
    """
    Guarda una imagen codificada en Base64 en el servidor.
    
    Args:
        id_cuestionario: ID del cuestionario
        id_pregunta: ID de la pregunta
        adjunto_base64: String Base64 de la imagen
    
    Returns:
        str: Ruta relativa (img/cuestionarios/c_1/pregunta_5_timestamp.jpg)
        None: Si no hay imagen o falla
    """
    if not adjunto_base64 or not adjunto_base64.startswith('data:image'):
        return None
    
    try:
        # Extraer tipo de imagen y datos
        match = re.match(r'data:image/(\w+);base64,(.+)', adjunto_base64)
        if not match:
            return None
        
        extension = match.group(1)
        datos_base64 = match.group(2)
        
        # Decodificar Base64
        datos_imagen = base64.b64decode(datos_base64)
        
        # Generar nombre único: pregunta_5_1638345678.jpg
        timestamp = int(time.time())
        nombre_archivo = f"pregunta_{id_pregunta}_{timestamp}.{extension}"
        
        # Crear carpeta: static/img/cuestionarios/c_1/
        carpeta = os.path.join(
            current_app.root_path, 
            'static', 
            'img', 
            'cuestionarios', 
            f'c_{id_cuestionario}'
        )
        os.makedirs(carpeta, exist_ok=True)
        
        # Guardar archivo
        ruta_completa = os.path.join(carpeta, nombre_archivo)
        with open(ruta_completa, 'wb') as f:
            f.write(datos_imagen)
        
        # Retornar ruta RELATIVA para la BD
        return f"img/cuestionarios/c_{id_cuestionario}/{nombre_archivo}"
        
    except Exception as e:
        print(f"Error guardando imagen: {e}")
        return None
```

---

## ✏️ FLUJO DE EDICIÓN

### **1. Usuario accede a editar**

```python
# routes_web.py - Línea 571
@app.route('/cuestionarios/<int:id_cuestionario>/editar')
@profesor_required
def cuestionarios_editar(id_cuestionario):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))

    # Obtener cuestionario COMPLETO (con preguntas y opciones)
    cuestionario_completo = cc.obtener_completo_por_id(id_cuestionario)

    if not cuestionario_completo:
        flash('El cuestionario no existe.', 'danger')
        return redirect(url_for('cuestionarios'))

    categorias = ctrl_cat.obtener_todas()

    return render_template(
        'mantenimiento_cuestionario.html',
        cuestionario_data=cuestionario_completo,  # ← Datos del cuestionario
        categorias=categorias
    )
```

---

### **2. CONTROLADOR: Obtener datos completos**

```python
# controladores/cuestionarios.py - Línea 217
def obtener_completo_por_id(id_cuestionario):
    """
    Obtiene cuestionario con todas sus preguntas y opciones anidadas.
    
    Returns:
        {
            'id_cuestionario': 5,
            'titulo': 'Matemáticas',
            'descripcion': '...',
            'preguntas': [
                {
                    'id_pregunta': 10,
                    'pregunta': '¿2+2?',
                    'opciones': [
                        {'id_opcion': 20, 'opcion': '3', 'es_correcta_bool': 0},
                        {'id_opcion': 21, 'opcion': '4', 'es_correcta_bool': 1}
                    ]
                }
            ]
        }
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # PASO 1: Obtener cuestionario
            cursor.execute(
                "SELECT * FROM CUESTIONARIO WHERE id_cuestionario = %s AND vigente = TRUE",
                (id_cuestionario,)
            )
            cuestionario_dict = cursor.fetchone()
            
            if not cuestionario_dict:
                return None
            
            # PASO 2: Obtener preguntas VIGENTES
            cursor.execute(
                "SELECT * FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1 ORDER BY num_pregunta",
                (id_cuestionario,)
            )
            preguntas = cursor.fetchall()
            
            # PASO 3: Para cada pregunta, obtener opciones VIGENTES
            for pregunta in preguntas:
                cursor.execute(
                    "SELECT * FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1",
                    (pregunta['id_pregunta'],)
                )
                opciones = cursor.fetchall()
                pregunta['opciones'] = opciones  # ← Anidar opciones
            
            cuestionario_dict['preguntas'] = preguntas
            
        return cuestionario_dict
    finally:
        conexion.close()
```

---

### **3. GUARDADO CON ACTUALIZACIÓN**

Cuando el usuario edita y guarda, el **mismo endpoint** `/api/cuestionarios/guardar-completo` maneja ambos casos (crear y editar) detectando si `id_cuestionario` está presente:

```python
# controladores/cuestionarios.py - Línea 348
def guardar_cuestionario_completo(data):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            
            id_cuestionario = data.get('id_cuestionario')
            
            # ══════════════════════════════════════════
            # CASO 2: ACTUALIZAR CUESTIONARIO EXISTENTE
            # ══════════════════════════════════════════
            if id_cuestionario:
                
                # --- PASO A: Actualizar datos del cuestionario ---
                sql_update = """
                    UPDATE CUESTIONARIO SET
                        titulo = %s, descripcion = %s, es_publico = %s,
                        id_categoria = %s, vigente = %s
                    WHERE id_cuestionario = %s
                """
                cursor.execute(sql_update, (
                    data['titulo'],
                    data['descripcion'],
                    data['es_publico'],
                    data['id_categoria'],
                    data.get('vigente', 1),
                    id_cuestionario
                ))
                
                # --- PASO B: Obtener IDs de preguntas existentes en BD ---
                cursor.execute(
                    "SELECT id_pregunta FROM PREGUNTAS WHERE id_cuestionario = %s AND vigente = 1",
                    (id_cuestionario,)
                )
                ids_preguntas_bd = {row['id_pregunta'] for row in cursor.fetchall()}
                
                ids_preguntas_data = set()  # IDs que vienen del frontend
                
                # --- PASO C: Procesar cada pregunta ---
                for index, pregunta_data in enumerate(data.get('preguntas', [])):
                    id_pregunta = pregunta_data.get('id_pregunta')
                    
                    # ---- C1: ACTUALIZAR pregunta existente ----
                    if id_pregunta and id_pregunta in ids_preguntas_bd:
                        ids_preguntas_data.add(id_pregunta)
                        
                        sql_update_pregunta = """
                            UPDATE PREGUNTAS SET
                                pregunta = %s, num_pregunta = %s,
                                puntaje_base = %s, tiempo = %s
                            WHERE id_pregunta = %s
                        """
                        cursor.execute(sql_update_pregunta, (
                            pregunta_data['pregunta'],
                            index + 1,
                            pregunta_data['puntaje_base'],
                            pregunta_data['tiempo'],
                            id_pregunta
                        ))
                        
                        # Guardar nueva imagen si cambió
                        if pregunta_data.get('adjunto') and pregunta_data['adjunto'].startswith('data:image'):
                            ruta_img = _guardar_imagen_base64(
                                id_cuestionario, 
                                id_pregunta, 
                                pregunta_data['adjunto']
                            )
                            if ruta_img:
                                cursor.execute(
                                    "UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s",
                                    (ruta_img, id_pregunta)
                                )
                        
                        # ---- C2: Procesar opciones de esta pregunta ----
                        cursor.execute(
                            "SELECT id_opcion FROM OPCIONES WHERE id_pregunta = %s AND vigente = 1",
                            (id_pregunta,)
                        )
                        ids_opciones_bd = {row['id_opcion'] for row in cursor.fetchall()}
                        ids_opciones_data = set()
                        
                        for opcion_data in pregunta_data.get('opciones', []):
                            id_opcion = opcion_data.get('id_opcion')
                            
                            # ACTUALIZAR opción existente
                            if id_opcion and id_opcion in ids_opciones_bd:
                                ids_opciones_data.add(id_opcion)
                                sql_update_opcion = """
                                    UPDATE OPCIONES SET
                                        opcion = %s, es_correcta_bool = %s,
                                        descripcion = %s, adjunto = %s
                                    WHERE id_opcion = %s
                                """
                                cursor.execute(sql_update_opcion, (
                                    opcion_data['opcion'],
                                    opcion_data['es_correcta_bool'],
                                    opcion_data.get('descripcion'),
                                    opcion_data.get('adjunto'),
                                    id_opcion
                                ))
                            else:
                                # INSERTAR nueva opción
                                sql_insert_opcion = """
                                    INSERT INTO OPCIONES 
                                    (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                                    VALUES (%s, %s, %s, %s, %s, 1)
                                """
                                cursor.execute(sql_insert_opcion, (
                                    id_pregunta,
                                    opcion_data['opcion'],
                                    opcion_data['es_correcta_bool'],
                                    opcion_data.get('descripcion'),
                                    opcion_data.get('adjunto')
                                ))
                        
                        # SOFT DELETE opciones que ya no existen
                        ids_opciones_eliminar = ids_opciones_bd - ids_opciones_data
                        for id_opcion_eliminar in ids_opciones_eliminar:
                            cursor.execute(
                                "UPDATE OPCIONES SET vigente = 0 WHERE id_opcion = %s",
                                (id_opcion_eliminar,)
                            )
                    
                    # ---- C3: INSERTAR nueva pregunta ----
                    else:
                        sql_insert_pregunta = """
                            INSERT INTO PREGUNTAS 
                            (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, vigente)
                            VALUES (%s, %s, %s, %s, %s, 1)
                        """
                        cursor.execute(sql_insert_pregunta, (
                            id_cuestionario,
                            pregunta_data['pregunta'],
                            index + 1,
                            pregunta_data['puntaje_base'],
                            pregunta_data['tiempo']
                        ))
                        id_pregunta_nueva = cursor.lastrowid
                        ids_preguntas_data.add(id_pregunta_nueva)
                        
                        # Guardar imagen si existe
                        ruta_img = _guardar_imagen_base64(
                            id_cuestionario, 
                            id_pregunta_nueva, 
                            pregunta_data.get('adjunto')
                        )
                        if ruta_img:
                            cursor.execute(
                                "UPDATE PREGUNTAS SET adjunto = %s WHERE id_pregunta = %s",
                                (ruta_img, id_pregunta_nueva)
                            )
                        
                        # Insertar opciones de la nueva pregunta
                        for opcion_data in pregunta_data.get('opciones', []):
                            sql_insert_opcion = """
                                INSERT INTO OPCIONES 
                                (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                                VALUES (%s, %s, %s, %s, %s, 1)
                            """
                            cursor.execute(sql_insert_opcion, (
                                id_pregunta_nueva,
                                opcion_data['opcion'],
                                opcion_data['es_correcta_bool'],
                                opcion_data.get('descripcion'),
                                opcion_data.get('adjunto')
                            ))
                
                # --- PASO D: SOFT DELETE preguntas que ya no existen ---
                ids_preguntas_eliminar = ids_preguntas_bd - ids_preguntas_data
                for id_pregunta_eliminar in ids_preguntas_eliminar:
                    # Marcar pregunta como no vigente
                    cursor.execute(
                        "UPDATE PREGUNTAS SET vigente = 0 WHERE id_pregunta = %s",
                        (id_pregunta_eliminar,)
                    )
                    # Marcar sus opciones como no vigentes
                    cursor.execute(
                        "UPDATE OPCIONES SET vigente = 0 WHERE id_pregunta = %s",
                        (id_pregunta_eliminar,)
                    )
        
        conexion.commit()
        return id_cuestionario
        
    except Exception as e:
        conexion.rollback()
        raise e
    finally:
        conexion.close()
```

**Algoritmo de sincronización:**

```
1. Obtener IDs de preguntas en BD: {10, 11, 12}
2. Obtener IDs de preguntas en frontend: {10, 12, 13}
3. Actualizar: 10, 12 (existen en ambos)
4. Insertar: 13 (nueva)
5. Soft delete: 11 (ya no existe en frontend)
```

---

## 📋 FLUJO DE CLONACIÓN

Permite a un profesor copiar un cuestionario público de otro profesor.

### **1. Usuario explora cuestionarios públicos**

```python
# routes_web.py - Línea 598
@app.route("/cuestionarios/explorar")
@profesor_required
def cuestionarios_explorar():
    id_usuario_actual = session['user_id']
    
    # Obtener cuestionarios públicos (excluyendo los propios)
    todos_cuestionarios = cc.obtener_publicos(excluir_usuario=id_usuario_actual)
    
    categorias = ctrl_cat.obtener_todas()
    
    return render_template(
        'explorar.html',
        cuestionarios=todos_cuestionarios,
        categorias=categorias
    )
```

---

### **2. Usuario hace clic en "Clonar"**

```python
# routes_web.py - Línea 619
@app.route('/cuestionarios/clonar/<int:id_cuestionario>', methods=['POST'])
@profesor_required
def clonar_cuestionario(id_cuestionario):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    
    id_usuario = session['user_id']
    
    # Llamar al controlador
    exito, resultado = cc.clonar_cuestionario(id_cuestionario, id_usuario)
    
    if exito:
        flash('¡Cuestionario clonado exitosamente!', 'success')
        return redirect(url_for('cuestionarios'))
    else:
        flash(resultado, 'danger')
        return redirect(url_for('dashboard'))
```

---

### **3. CONTROLADOR: Lógica de clonación**

```python
# controladores/cuestionarios.py - Línea 549
def clonar_cuestionario(id_cuestionario_original, id_usuario_nuevo):
    """
    Clona un cuestionario completo para un nuevo usuario.
    El clon se crea como NO público por defecto.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            
            # --- PASO 1: Obtener datos del cuestionario original ---
            cursor.execute("""
                SELECT titulo, descripcion, id_categoria, id_usuario
                FROM CUESTIONARIO
                WHERE id_cuestionario = %s
            """, (id_cuestionario_original,))
            cuestionario_orig = cursor.fetchone()
            
            if not cuestionario_orig:
                return False, "El cuestionario no existe."
            
            # --- PASO 2: Verificar que no sea el mismo creador ---
            if cuestionario_orig['id_usuario'] == id_usuario_nuevo:
                return False, "No puedes clonar tu propio cuestionario."
            
            # --- PASO 3: Verificar que esté publicado ---
            cursor.execute(
                "SELECT vigente FROM CUESTIONARIO WHERE id_cuestionario = %s",
                (id_cuestionario_original,)
            )
            estado = cursor.fetchone()
            if not estado or estado['vigente'] != 1:
                return False, "Solo se pueden clonar cuestionarios publicados."
            
            # --- PASO 4: Crear nuevo cuestionario ---
            nuevo_titulo = f"{cuestionario_orig['titulo']} (Copia)"
            cursor.execute("""
                INSERT INTO CUESTIONARIO 
                (titulo, descripcion, es_publico, fecha_hora_creacion,
                 id_usuario, id_categoria, id_cuestionario_original, vigente)
                VALUES (%s, %s, 0, NOW(), %s, %s, %s, 1)
            """, (
                nuevo_titulo,
                cuestionario_orig['descripcion'],
                id_usuario_nuevo,
                cuestionario_orig['id_categoria'],
                id_cuestionario_original  # ← Registro de origen
            ))
            
            id_cuestionario_nuevo = cursor.lastrowid
            
            # --- PASO 5: Clonar preguntas ---
            cursor.execute("""
                SELECT id_pregunta, pregunta, num_pregunta, puntaje_base, tiempo, adjunto, vigente
                FROM PREGUNTAS
                WHERE id_cuestionario = %s AND vigente = 1
                ORDER BY num_pregunta
            """, (id_cuestionario_original,))
            preguntas = cursor.fetchall()
            
            for pregunta in preguntas:
                # Insertar pregunta clonada
                cursor.execute("""
                    INSERT INTO PREGUNTAS 
                    (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, adjunto, vigente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    id_cuestionario_nuevo,
                    pregunta['pregunta'],
                    pregunta['num_pregunta'],
                    pregunta['puntaje_base'],
                    pregunta['tiempo'],
                    pregunta['adjunto'],
                    pregunta['vigente']
                ))
                
                id_pregunta_nueva = cursor.lastrowid
                
                # --- PASO 6: Clonar opciones ---
                cursor.execute("""
                    SELECT opcion, es_correcta_bool, descripcion, adjunto, vigente
                    FROM OPCIONES
                    WHERE id_pregunta = %s AND vigente = 1
                """, (pregunta['id_pregunta'],))
                opciones = cursor.fetchall()
                
                for opcion in opciones:
                    cursor.execute("""
                        INSERT INTO OPCIONES 
                        (id_pregunta, opcion, es_correcta_bool, descripcion, adjunto, vigente)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        id_pregunta_nueva,
                        opcion['opcion'],
                        opcion['es_correcta_bool'],
                        opcion['descripcion'],
                        opcion['adjunto'],
                        opcion['vigente']
                    ))
        
        conexion.commit()
        return True, id_cuestionario_nuevo
        
    except Exception as e:
        conexion.rollback()
        return False, f"Error al clonar: {str(e)}"
    finally:
        conexion.close()
```

**Características del clon:**
- ✅ Título con sufijo " (Copia)"
- ✅ `es_publico = 0` (privado por defecto)
- ✅ `id_cuestionario_original` apunta al original
- ✅ Nuevo `id_usuario` (el que clona)
- ✅ Copia TODAS las preguntas y opciones vigentes

---

## 🗑️ SOFT DELETE Y VIGENCIA

DogeHoot usa **eliminación lógica** (soft delete) en lugar de eliminar físicamente los datos.

### **¿Por qué?**

1. **Historial de partidas**: Las partidas guardadas referencian preguntas/opciones. Si se eliminan físicamente, se pierden los datos históricos.
2. **Auditoría**: Permite recuperar datos borrados accidentalmente.
3. **Integridad referencial**: Evita problemas de foreign keys.

### **Columna `vigente`**

- `vigente = 1` → Activo (se muestra)
- `vigente = 0` → Eliminado (no se muestra, pero existe en BD)

### **Ejemplo: Eliminar cuestionario**

```python
# controladores/cuestionarios.py - Línea 295
def desactivar(id_cuestionario):
    """Soft delete: marca como no vigente."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE CUESTIONARIO SET vigente = FALSE WHERE id_cuestionario = %s"
            cursor.execute(sql, (id_cuestionario,))
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        conexion.close()
```

**Cascada de soft delete:**
```
Eliminar cuestionario → vigente=0
    └─→ Sus preguntas → vigente=0
        └─→ Sus opciones → vigente=0
```

### **Queries siempre filtran por vigente**

```sql
-- ✅ CORRECTO
SELECT * FROM CUESTIONARIO WHERE vigente = TRUE;
SELECT * FROM PREGUNTAS WHERE id_cuestionario = 5 AND vigente = 1;

-- ❌ INCORRECTO (mostraría eliminados)
SELECT * FROM CUESTIONARIO;
```

---

## 🔌 ENDPOINTS API

### **Resumen de rutas**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/cuestionarios` | Listar cuestionarios |
| GET | `/api/cuestionarios/<id>` | Obtener uno por ID |
| POST | `/api/cuestionarios` | Crear cuestionario básico |
| PUT | `/api/cuestionarios` | Actualizar cuestionario básico |
| DELETE | `/api/cuestionarios/<id>` | Soft delete |
| POST | `/api/cuestionarios/guardar-completo` | Crear/actualizar completo (con preguntas y opciones) |
| POST | `/api/cuestionarios/guardar-basico` | Crear solo datos básicos (sin preguntas) |
| GET | `/api/cuestionarios/<id>/preguntas` | Obtener preguntas de un cuestionario |
| POST | `/api/cuestionarios/<id>/preguntas` | Agregar pregunta |
| PUT | `/api/preguntas/<id>` | Actualizar pregunta |
| DELETE | `/api/preguntas/<id>` | Eliminar pregunta |
| POST | `/api/preguntas/<id>/imagen` | Subir imagen a pregunta |
| DELETE | `/api/preguntas/<id>/imagen` | Eliminar imagen |

**Autenticación:**
- Todos los endpoints requieren `@jwt_required()` (token JWT en header)

---

## 📊 ESQUEMA DE BASE DE DATOS

```sql
CREATE TABLE CUESTIONARIO (
    id_cuestionario INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    es_publico TINYINT(1) DEFAULT 0,  -- 0=Privado, 1=Público
    fecha_hora_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    id_categoria INT,
    id_cuestionario_original INT,  -- Para clones
    vigente TINYINT(1) DEFAULT 1,  -- Soft delete
    
    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),
    FOREIGN KEY (id_categoria) REFERENCES CATEGORIA(id_categoria),
    FOREIGN KEY (id_cuestionario_original) REFERENCES CUESTIONARIO(id_cuestionario)
);

CREATE TABLE PREGUNTAS (
    id_pregunta INT AUTO_INCREMENT PRIMARY KEY,
    id_cuestionario INT NOT NULL,
    pregunta TEXT NOT NULL,
    num_pregunta INT NOT NULL,  -- Orden (1, 2, 3...)
    puntaje_base INT DEFAULT 100,
    tiempo SMALLINT DEFAULT 15,  -- Segundos
    adjunto VARCHAR(255),  -- Ruta de imagen
    vigente TINYINT(1) DEFAULT 1,
    
    FOREIGN KEY (id_cuestionario) REFERENCES CUESTIONARIO(id_cuestionario)
);

CREATE TABLE OPCIONES (
    id_opcion INT AUTO_INCREMENT PRIMARY KEY,
    id_pregunta INT NOT NULL,
    opcion VARCHAR(200) NOT NULL,
    es_correcta_bool TINYINT(1) DEFAULT 0,  -- 0=Incorrecta, 1=Correcta
    descripcion TEXT,
    adjunto TEXT,
    vigente TINYINT(1) DEFAULT 1,
    
    FOREIGN KEY (id_pregunta) REFERENCES PREGUNTAS(id_pregunta)
);
```

---

## 🔍 CASOS DE USO COMPLETOS

### **Caso 1: Profesor crea cuestionario desde cero**

```
1. GET /cuestionarios/nuevo
   └─→ Renderiza formulario vacío
   
2. Usuario llena formulario:
   - Título: "Matemáticas Básicas"
   - Categoría: "Ciencias"
   - 3 preguntas con 4 opciones cada una
   
3. POST /api/cuestionarios/guardar-completo
   {
     "id_cuestionario": null,  ← NUEVO
     "titulo": "Matemáticas Básicas",
     ...
   }
   
4. Controlador:
   - INSERT INTO CUESTIONARIO → id=15
   - INSERT INTO PREGUNTAS (3 filas) → ids: 50, 51, 52
   - INSERT INTO OPCIONES (12 filas) → ids: 200-211
   
5. COMMIT → Éxito
   
6. Respuesta:
   {
     "ok": true,
     "id_cuestionario": 15
   }
```

---

### **Caso 2: Profesor edita cuestionario existente**

```
1. GET /cuestionarios/15/editar
   └─→ Llama a obtener_completo_por_id(15)
   └─→ Renderiza formulario pre-llenado
   
2. Usuario modifica:
   - Cambia título
   - Elimina pregunta #2
   - Agrega nueva pregunta #4
   - Modifica opción en pregunta #1
   
3. POST /api/cuestionarios/guardar-completo
   {
     "id_cuestionario": 15,  ← EDICIÓN
     "preguntas": [
       { "id_pregunta": 50, ... },  ← Actualizar
       { "id_pregunta": null, ... },  ← Insertar (nueva)
       // Pregunta 51 no está → Eliminar
     ]
   }
   
4. Controlador:
   - UPDATE CUESTIONARIO SET titulo=...
   - UPDATE PREGUNTAS id=50
   - INSERT PREGUNTAS → id=53 (nueva)
   - UPDATE PREGUNTAS SET vigente=0 WHERE id=51 (soft delete)
   - UPDATE OPCIONES SET vigente=0 WHERE id_pregunta=51
   
5. COMMIT → Éxito
```

---

### **Caso 3: Profesor clona cuestionario de otro**

```
1. GET /cuestionarios/explorar
   └─→ Muestra cuestionarios públicos
   
2. Usuario hace clic en "Clonar" en cuestionario id=20
   
3. POST /cuestionarios/clonar/20
   
4. Controlador:
   - Valida que no sea el mismo creador
   - Valida que esté publicado (vigente=1)
   - INSERT CUESTIONARIO (nuevo) → id=25
     * titulo = "Original (Copia)"
     * es_publico = 0
     * id_usuario = 10 (el que clona)
     * id_cuestionario_original = 20
   - Copia 5 preguntas → ids: 60-64
   - Copia 20 opciones → ids: 300-319
   
5. COMMIT → Éxito
   
6. Redirección a "Mis Cuestionarios"
   └─→ Aparece "Original (Copia)" como privado
```

---

## 🎯 PUNTOS CLAVE DEL CÓDIGO

### **1. Transacciones atómicas**

Todo el guardado ocurre en una **única transacción**:

```python
try:
    cursor.execute(...)  # Cuestionario
    cursor.execute(...)  # Preguntas
    cursor.execute(...)  # Opciones
    conexion.commit()  # ✅ Todo o nada
except:
    conexion.rollback()  # ❌ Revertir si falla
```

### **2. Uso de `lastrowid`**

Para obtener el ID del registro recién insertado:

```python
cursor.execute("INSERT INTO CUESTIONARIO ...")
id_nuevo = cursor.lastrowid  # ← ID auto-generado
```

### **3. Soft delete en cascada**

```python
# Eliminar pregunta → eliminar sus opciones
cursor.execute("UPDATE PREGUNTAS SET vigente=0 WHERE id_pregunta=%s", (id,))
cursor.execute("UPDATE OPCIONES SET vigente=0 WHERE id_pregunta=%s", (id,))
```

### **4. Sincronización con sets**

```python
ids_bd = {1, 2, 3}      # En base de datos
ids_data = {1, 3, 4}    # Del frontend

actualizar = ids_bd & ids_data  # {1, 3}
insertar = ids_data - ids_bd    # {4}
eliminar = ids_bd - ids_data    # {2}
```

### **5. Decoradores de seguridad**

```python
@app.route("/cuestionarios")
@profesor_required  # ← Solo profesores
def cuestionarios():
    ...
```

---

## 📝 RESUMEN EJECUTIVO

1. **Crear**: Frontend → API → Controlador INSERT → COMMIT
2. **Editar**: Obtener datos → Modificar → Detectar cambios (UPDATE/INSERT/DELETE) → COMMIT
3. **Clonar**: Copiar estructura completa a nuevo usuario → COMMIT
4. **Eliminar**: Soft delete (vigente=0) en cascada
5. **Listar**: Siempre filtrar por `vigente=1`

**Ventajas del diseño:**
- ✅ Transacciones atómicas (todo o nada)
- ✅ Soft delete (no pierde historial)
- ✅ Sincronización inteligente (UPDATE vs INSERT)
- ✅ Imágenes guardadas en servidor con nombres únicos
- ✅ Clonación preserva referencia al original

---

**¿Qué sigue?** 🚀

En el próximo documento veremos el **Flujo de Juego en Tiempo Real** (ajax_game.py) con manejo de estado en memoria y sincronización de participantes.
