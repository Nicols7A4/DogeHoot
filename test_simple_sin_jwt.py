#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba simple SIN JWT para verificar que las rutas existen
"""

import sys
import os

# Agregar el directorio mysite al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mysite'))

from main import app

print("\n" + "="*60)
print("VERIFICANDO RUTAS DE LAS APIS CRUD")
print("="*60)

# Obtener todas las rutas registradas
routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
        'path': str(rule)
    })

# Filtrar y mostrar rutas de PARTIDAS
print("\n📦 RUTAS DE PARTIDAS:")
partida_routes = [r for r in routes if 'partida' in r['path'].lower() and 'api_' in r['endpoint']]
for r in sorted(partida_routes, key=lambda x: x['path']):
    print(f"   {r['methods']:12} {r['path']:50} → {r['endpoint']}")

# Filtrar y mostrar rutas de SKINS
print("\n🎨 RUTAS DE SKINS:")
skin_routes = [r for r in routes if 'skin' in r['path'].lower() and 'api_' in r['endpoint']]
for r in sorted(skin_routes, key=lambda x: x['path']):
    print(f"   {r['methods']:12} {r['path']:50} → {r['endpoint']}")

# Filtrar y mostrar rutas de CATEGORIAS
print("\n📁 RUTAS DE CATEGORIAS:")
categoria_routes = [r for r in routes if 'categoria' in r['path'].lower() and 'api_' in r['endpoint']]
for r in sorted(categoria_routes, key=lambda x: x['path']):
    print(f"   {r['methods']:12} {r['path']:50} → {r['endpoint']}")

print("\n" + "="*60)
print(f"✅ Total de rutas API encontradas:")
print(f"   - Partidas: {len(partida_routes)}")
print(f"   - Skins: {len(skin_routes)}")
print(f"   - Categorías: {len(categoria_routes)}")
print("="*60 + "\n")
