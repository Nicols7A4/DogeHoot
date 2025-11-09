#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para las APIs CRUD de PARTIDA, SKINS y CATEGORIA
Requiere que el servidor Flask esté corriendo en http://localhost:5001
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

# Primero necesitamos obtener un token JWT
def obtener_token():
    """Intenta autenticarse y obtener un token JWT"""
    try:
        # Flask-JWT usa 'username' y 'password' por defecto en el endpoint /auth
        # Pero tu authenticate() espera 'correo' y 'password'
        # Vamos a probar ambos formatos
        
        # Primero intentamos con un usuario que probablemente exista
        credenciales = [
            {"username": "admin@dogehoot.com", "password": "admin123"},
            {"username": "test@test.com", "password": "test123"},
            {"username": "usuario@test.com", "password": "123456"},
        ]
        
        for cred in credenciales:
            response = requests.post(
                f"{BASE_URL}/auth",
                json=cred,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                token = response.json().get('access_token')
                print(f"✅ Token obtenido exitosamente con usuario: {cred['username']}")
                return token
        
        # Si ninguna credencial funcionó, mostrar el último error
        print(f"❌ No se pudo obtener token con ninguna credencial")
        print(f"   Último status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
        
    except Exception as e:
        print(f"❌ Excepción al obtener token: {e}")
        return None

def hacer_request(metodo, endpoint, token, data=None):
    """Función auxiliar para hacer requests con token JWT"""
    headers = {
        'Authorization': f'JWT {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if metodo == 'GET':
            response = requests.get(url, headers=headers)
        elif metodo == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif metodo == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif metodo == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        return response
    except Exception as e:
        print(f"❌ Error en request: {e}")
        return None

# ========================================
# PRUEBAS PARA SKINS
# ========================================

def test_skins(token):
    print("\n" + "="*60)
    print("PRUEBAS DE APIS CRUD - SKINS")
    print("="*60)
    
    # 1. CREAR SKIN
    print("\n1️⃣  Creando nueva skin...")
    nueva_skin = {
        "nombre": "Skin de Prueba",
        "ruta": "/img/skins/test_skin.png",
        "precio": 100,
        "vigente": 1
    }
    response = hacer_request('POST', '/api_registrarskin', token, nueva_skin)
    if response and response.status_code == 201:
        skin_id = response.json()['data']['id_skin']
        print(f"   ✅ Skin creada con ID: {skin_id}")
    else:
        print(f"   ❌ Error creando skin: {response.status_code if response else 'Sin respuesta'}")
        if response:
            print(f"      Response: {response.text}")
        return
    
    # 2. OBTENER TODAS LAS SKINS
    print("\n2️⃣  Obteniendo todas las skins...")
    response = hacer_request('GET', '/api_obtenerskins', token)
    if response and response.status_code == 200:
        skins = response.json()['data']
        print(f"   ✅ Se obtuvieron {len(skins)} skins")
    else:
        print(f"   ❌ Error obteniendo skins: {response.status_code if response else 'Sin respuesta'}")
    
    # 3. OBTENER SKIN POR ID
    print(f"\n3️⃣  Obteniendo skin con ID {skin_id}...")
    response = hacer_request('GET', f'/api_obtenerskinporid/{skin_id}', token)
    if response and response.status_code == 200:
        skin = response.json()['data']
        print(f"   ✅ Skin obtenida: {skin['nombre']}")
    else:
        print(f"   ❌ Error obteniendo skin: {response.status_code if response else 'Sin respuesta'}")
    
    # 4. ACTUALIZAR SKIN
    print(f"\n4️⃣  Actualizando skin con ID {skin_id}...")
    datos_actualizados = {
        "nombre": "Skin Actualizada",
        "precio": 150
    }
    response = hacer_request('PUT', f'/api_actualizarskin/{skin_id}', token, datos_actualizados)
    if response and response.status_code == 200:
        print(f"   ✅ Skin actualizada correctamente")
    else:
        print(f"   ❌ Error actualizando skin: {response.status_code if response else 'Sin respuesta'}")
    
    # 5. ELIMINAR SKIN
    print(f"\n5️⃣  Eliminando skin con ID {skin_id}...")
    response = hacer_request('DELETE', f'/api_eliminarskin/{skin_id}', token)
    if response and response.status_code == 200:
        print(f"   ✅ Skin eliminada correctamente")
    else:
        print(f"   ❌ Error eliminando skin: {response.status_code if response else 'Sin respuesta'}")

# ========================================
# PRUEBAS PARA CATEGORIAS
# ========================================

def test_categorias(token):
    print("\n" + "="*60)
    print("PRUEBAS DE APIS CRUD - CATEGORIAS")
    print("="*60)
    
    # 1. CREAR CATEGORIA
    print("\n1️⃣  Creando nueva categoría...")
    nueva_categoria = {
        "categoria": "Categoría de Prueba"
    }
    response = hacer_request('POST', '/api_registrarcategoria', token, nueva_categoria)
    if response and response.status_code == 201:
        categoria_id = response.json()['data']['id_categoria']
        print(f"   ✅ Categoría creada con ID: {categoria_id}")
    else:
        print(f"   ❌ Error creando categoría: {response.status_code if response else 'Sin respuesta'}")
        if response:
            print(f"      Response: {response.text}")
        return
    
    # 2. OBTENER TODAS LAS CATEGORIAS
    print("\n2️⃣  Obteniendo todas las categorías...")
    response = hacer_request('GET', '/api_obtenercategorias', token)
    if response and response.status_code == 200:
        categorias = response.json()['data']
        print(f"   ✅ Se obtuvieron {len(categorias)} categorías")
    else:
        print(f"   ❌ Error obteniendo categorías: {response.status_code if response else 'Sin respuesta'}")
    
    # 3. OBTENER CATEGORIA POR ID
    print(f"\n3️⃣  Obteniendo categoría con ID {categoria_id}...")
    response = hacer_request('GET', f'/api_obtenercategoriaporid/{categoria_id}', token)
    if response and response.status_code == 200:
        categoria = response.json()['data']
        print(f"   ✅ Categoría obtenida: {categoria['categoria']}")
    else:
        print(f"   ❌ Error obteniendo categoría: {response.status_code if response else 'Sin respuesta'}")
    
    # 4. ACTUALIZAR CATEGORIA
    print(f"\n4️⃣  Actualizando categoría con ID {categoria_id}...")
    datos_actualizados = {
        "categoria": "Categoría Actualizada"
    }
    response = hacer_request('PUT', f'/api_actualizarcategoria/{categoria_id}', token, datos_actualizados)
    if response and response.status_code == 200:
        print(f"   ✅ Categoría actualizada correctamente")
    else:
        print(f"   ❌ Error actualizando categoría: {response.status_code if response else 'Sin respuesta'}")
    
    # 5. ELIMINAR CATEGORIA
    print(f"\n5️⃣  Eliminando categoría con ID {categoria_id}...")
    response = hacer_request('DELETE', f'/api_eliminarcategoria/{categoria_id}', token)
    if response and response.status_code == 200:
        print(f"   ✅ Categoría eliminada correctamente")
    else:
        print(f"   ❌ Error eliminando categoría: {response.status_code if response else 'Sin respuesta'}")

# ========================================
# PRUEBAS PARA PARTIDAS
# ========================================

def test_partidas(token):
    print("\n" + "="*60)
    print("PRUEBAS DE APIS CRUD - PARTIDAS")
    print("="*60)
    
    # 1. CREAR PARTIDA
    print("\n1️⃣  Creando nueva partida...")
    nueva_partida = {
        "pin": "TEST01",
        "id_cuestionario": 1,
        "modalidad": "individual",
        "estado": "E",
        "fecha_hora_inicio": datetime.now().isoformat(),
        "cant_grupos": 0,
        "recompensas_otorgadas": 0
    }
    response = hacer_request('POST', '/api_registrarpartida', token, nueva_partida)
    if response and response.status_code == 201:
        partida_id = response.json()['data']['id_partida']
        print(f"   ✅ Partida creada con ID: {partida_id}")
    else:
        print(f"   ❌ Error creando partida: {response.status_code if response else 'Sin respuesta'}")
        if response:
            print(f"      Response: {response.text}")
        return
    
    # 2. OBTENER TODAS LAS PARTIDAS
    print("\n2️⃣  Obteniendo todas las partidas...")
    response = hacer_request('GET', '/api_obtenerpartidas', token)
    if response and response.status_code == 200:
        partidas = response.json()['data']
        print(f"   ✅ Se obtuvieron {len(partidas)} partidas")
    else:
        print(f"   ❌ Error obteniendo partidas: {response.status_code if response else 'Sin respuesta'}")
    
    # 3. OBTENER PARTIDA POR ID
    print(f"\n3️⃣  Obteniendo partida con ID {partida_id}...")
    response = hacer_request('GET', f'/api_obtenerpartidaporid/{partida_id}', token)
    if response and response.status_code == 200:
        partida = response.json()['data']
        print(f"   ✅ Partida obtenida: PIN {partida['pin']}")
    else:
        print(f"   ❌ Error obteniendo partida: {response.status_code if response else 'Sin respuesta'}")
    
    # 4. ACTUALIZAR PARTIDA
    print(f"\n4️⃣  Actualizando partida con ID {partida_id}...")
    datos_actualizados = {
        "estado": "P",
        "cant_grupos": 2
    }
    response = hacer_request('PUT', f'/api_actualizarpartida/{partida_id}', token, datos_actualizados)
    if response and response.status_code == 200:
        print(f"   ✅ Partida actualizada correctamente")
    else:
        print(f"   ❌ Error actualizando partida: {response.status_code if response else 'Sin respuesta'}")
    
    # 5. ELIMINAR PARTIDA
    print(f"\n5️⃣  Eliminando partida con ID {partida_id}...")
    response = hacer_request('DELETE', f'/api_eliminarpartida/{partida_id}', token)
    if response and response.status_code == 200:
        print(f"   ✅ Partida eliminada correctamente")
    else:
        print(f"   ❌ Error eliminando partida: {response.status_code if response else 'Sin respuesta'}")

# ========================================
# FUNCIÓN PRINCIPAL
# ========================================

def main():
    print("\n" + "="*60)
    print("INICIANDO PRUEBAS DE APIS CRUD")
    print("="*60)
    print("\n⚠️  Asegúrate de que el servidor Flask esté corriendo en:")
    print(f"   {BASE_URL}")
    print("\n🔑 Intentando obtener token de autenticación...")
    
    token = obtener_token()
    
    if not token:
        print("\n❌ No se pudo obtener el token. Verifica:")
        print("   1. Que el servidor Flask esté corriendo")
        print("   2. Que las credenciales sean correctas")
        print("   3. Que el endpoint /auth esté disponible")
        return
    
    # Ejecutar pruebas
    try:
        test_skins(token)
        test_categorias(token)
        test_partidas(token)
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
