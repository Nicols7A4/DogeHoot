import sys
import os
from datetime import datetime

# ⭐ Agregar automáticamente la carpeta mysite al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bd import obtener_conexion
from controladores.usuarios import encriptar_sha256

def print_usuarios_contraseñas():
    conexion = obtener_conexion()
    usuarios = []
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_usuario, correo, nombre_usuario, contraseña FROM USUARIO WHERE VIGENTE = true")
            usuarios = cursor.fetchall()
    finally:
        if conexion: 
            conexion.close()
        
    return usuarios

if __name__ == "__main__":
    usuarios = print_usuarios_contraseñas()
    
    # Crear nombre del archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = os.path.join(os.path.dirname(__file__), f"usuarios_contraseñas_{timestamp}.txt")
    
    # Preparar contenido
    contenido = []
    contenido.append("=" * 60)
    contenido.append("📋 USUARIOS Y CONTRASEÑAS")
    contenido.append("=" * 60)
    contenido.append("")
    
    for usuario in usuarios:
        contenido.append(f"🆔 Id USUARIO: {usuario['id_usuario']}")
        contenido.append(f"👤 Usuario: {usuario['nombre_usuario']}")
        contenido.append(f"   📧 Correo: {usuario['correo']}")
        contenido.append(f"   🔑 Contraseña: {usuario['contraseña']}")
        contenido.append("-" * 60)
    
    contenido.append("")
    contenido.append(f"Total de usuarios: {len(usuarios)}")
    contenido.append(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Imprimir en consola
    print("\n".join(contenido))
    
    # Guardar en archivo
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write("\n".join(contenido))
        print(f"\n✅ Archivo guardado exitosamente en:")
        print(f"   {archivo_salida}")
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo: {e}")
