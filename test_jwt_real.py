#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba REAL con JWT para las APIs CRUD de SKINS y CATEGORIA
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mysite'))

from bd import obtener_conexion
from datetime import datetime
import json

print("\n" + "="*60)
print("PRUEBAS REALES CON JWT - SKINS Y CATEGORIAS")
print("="*60)

# Primero verificar si hay usuarios en la BD
print("\n1️⃣  Verificando usuarios en la base de datos...")
import pymysql.cursors
conexion = obtener_conexion()
try:
    with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id_usuario, correo, nombre_usuario, verificado FROM USUARIO WHERE vigente = 1 LIMIT 5")
        usuarios = cursor.fetchall()
        
        if usuarios:
            print(f"   ✅ Se encontraron {len(usuarios)} usuarios:")
            for u in usuarios:
                print(f"      - ID: {u['id_usuario']}, Correo: {u['correo']}, Usuario: {u['nombre_usuario']}, Verificado: {u['verificado']}")
        else:
            print("   ⚠️  No se encontraron usuarios. Creando usuario de prueba...")
            
            # Crear usuario de prueba
            cursor.execute("""
                INSERT INTO USUARIO (nombre_completo, nombre_usuario, correo, contraseña, tipo, verificado, vigente)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ("Usuario Prueba", "test_user", "test@test.com", "test123", "E", 1, 1))
            conexion.commit()
            print("   ✅ Usuario de prueba creado: test@test.com / test123")
            
finally:
    conexion.close()

print("\n2️⃣  Probando autenticación JWT...")
print("   ⚠️  Usando usuario real de la BD...")

# Obtener contraseña de un usuario verificado
conexion = obtener_conexion()
usuario_test = None
try:
    with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT correo, contraseña FROM USUARIO WHERE vigente = 1 AND verificado = 1 LIMIT 1")
        usuario_test = cursor.fetchone()
finally:
    conexion.close()

if not usuario_test:
    print("   ❌ No hay usuarios verificados en la BD")
    sys.exit(1)

print(f"   Usuario: {usuario_test['correo']}")

from main import app

with app.test_client() as client:
    # Intentar autenticarse con usuario real
    credenciales = [
        {"username": usuario_test['correo'], "password": usuario_test['contraseña']},
    ]
    
    token = None
    for cred in credenciales:
        print(f"   Intentando con: {cred['username']}")
        response = client.post('/auth',
            data=json.dumps(cred),
            content_type='application/json')
        
        if response.status_code == 200:
            token = response.json.get('access_token')
            print(f"   ✅ Token JWT obtenido exitosamente")
            print(f"   Token: {token[:50]}...")
            break
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
    
    if not token:
        print("\n❌ No se pudo obtener token JWT. Abortando pruebas.")
        sys.exit(1)
    
    headers = {
        'Authorization': f'JWT {token}',
        'Content-Type': 'application/json'
    }
    
    # ========================================
    # PRUEBAS DE SKINS
    # ========================================
    
    print("\n" + "="*60)
    print("PRUEBAS DE APIS CRUD - SKINS")
    print("="*60)
    
    # 1. CREAR SKIN
    print("\n3️⃣  Creando nueva skin...")
    nueva_skin = {
        "ruta": "img/skins/test_jwt.png",
        "tipo": "marco",
        "precio": 200,
        "vigente": 1
    }
    response = client.post('/api_registrarskin',
        data=json.dumps(nueva_skin),
        headers=headers)
    
    if response.status_code == 201:
        skin_id = response.json['data']['id_skin']
        print(f"   ✅ Skin creada con ID: {skin_id}")
        print(f"   Response: {response.json}")
    else:
        print(f"   ❌ Error {response.status_code}")
        print(f"   Response: {response.data.decode()}")
        skin_id = None
    
    # 2. OBTENER TODAS LAS SKINS
    print("\n4️⃣  Obteniendo todas las skins...")
    response = client.get('/api_obtenerskins', headers=headers)
    
    if response.status_code == 200:
        skins = response.json['data']
        print(f"   ✅ Se obtuvieron {len(skins)} skins")
        if skins:
            print(f"   Primera skin: {skins[0]}")
    else:
        print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
    
    # 3. OBTENER SKIN POR ID
    if skin_id:
        print(f"\n5️⃣  Obteniendo skin con ID {skin_id}...")
        response = client.get(f'/api_obtenerskinporid/{skin_id}', headers=headers)
        
        if response.status_code == 200:
            skin = response.json['data']
            print(f"   ✅ Skin obtenida: {skin['ruta']} (tipo: {skin.get('tipo', 'N/A')})")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
        
        # 4. ACTUALIZAR SKIN
        print(f"\n6️⃣  Actualizando skin con ID {skin_id}...")
        datos_actualizados = {
            "tipo": "fondo",
            "precio": 250
        }
        response = client.put(f'/api_actualizarskin/{skin_id}',
            data=json.dumps(datos_actualizados),
            headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Skin actualizada correctamente")
            print(f"   Response: {response.json}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
        
        # 5. ELIMINAR SKIN
        print(f"\n7️⃣  Eliminando skin con ID {skin_id}...")
        response = client.delete(f'/api_eliminarskin/{skin_id}', headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Skin eliminada correctamente")
            print(f"   Response: {response.json}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
    
    # ========================================
    # PRUEBAS DE CATEGORIAS
    # ========================================
    
    print("\n" + "="*60)
    print("PRUEBAS DE APIS CRUD - CATEGORIAS")
    print("="*60)
    
    # 1. CREAR CATEGORIA
    print("\n8️⃣  Creando nueva categoría...")
    nueva_categoria = {
        "categoria": "Categoria Test JWT"
    }
    response = client.post('/api_registrarcategoria',
        data=json.dumps(nueva_categoria),
        headers=headers)
    
    if response.status_code == 201:
        categoria_id = response.json['data']['id_categoria']
        print(f"   ✅ Categoría creada con ID: {categoria_id}")
        print(f"   Response: {response.json}")
    else:
        print(f"   ❌ Error {response.status_code}")
        print(f"   Response: {response.data.decode()}")
        categoria_id = None
    
    # 2. OBTENER TODAS LAS CATEGORIAS
    print("\n9️⃣  Obteniendo todas las categorías...")
    response = client.get('/api_obtenercategorias', headers=headers)
    
    if response.status_code == 200:
        categorias = response.json['data']
        print(f"   ✅ Se obtuvieron {len(categorias)} categorías")
        if categorias:
            print(f"   Primera categoría: {categorias[0]}")
    else:
        print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
    
    # 3. OBTENER CATEGORIA POR ID
    if categoria_id:
        print(f"\n🔟 Obteniendo categoría con ID {categoria_id}...")
        response = client.get(f'/api_obtenercategoriaporid/{categoria_id}', headers=headers)
        
        if response.status_code == 200:
            categoria = response.json['data']
            print(f"   ✅ Categoría obtenida: {categoria['categoria']}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
        
        # 4. ACTUALIZAR CATEGORIA
        print(f"\n1️⃣1️⃣  Actualizando categoría con ID {categoria_id}...")
        datos_actualizados = {
            "categoria": "Categoria Test JWT Actualizada"
        }
        response = client.put(f'/api_actualizarcategoria/{categoria_id}',
            data=json.dumps(datos_actualizados),
            headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Categoría actualizada correctamente")
            print(f"   Response: {response.json}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")
        
        # 5. ELIMINAR CATEGORIA
        print(f"\n1️⃣2️⃣  Eliminando categoría con ID {categoria_id}...")
        response = client.delete(f'/api_eliminarcategoria/{categoria_id}', headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Categoría eliminada correctamente")
            print(f"   Response: {response.json}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.data.decode()}")

print("\n" + "="*60)
print("✅ PRUEBAS CON JWT COMPLETADAS")
print("="*60 + "\n")
