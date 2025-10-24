"""
SCRIPT DE PRUEBA - Google Drive Uploader
=========================================
Prueba la subida de archivos a Google Drive

Autor: DogeHoot Team
Fecha: 23 de octubre de 2025
"""

import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controladores.google_drive_uploader import GoogleDriveUploader, subir_archivo_rapido


def probar_subida_basica():
    """Prueba básica de subida de archivo"""
    print("\n" + "="*60)
    print("🚀 PRUEBA 1: Subida Básica de Archivo")
    print("="*60)
    
    # Crear un archivo de prueba
    archivo_prueba = "test_drive.txt"
    with open(archivo_prueba, 'w', encoding='utf-8') as f:
        f.write("¡Hola desde DogeHoot! 🐕\n")
        f.write("Este es un archivo de prueba para Google Drive\n")
        f.write("Fecha: 23 de octubre de 2025\n")
    
    print(f"📄 Archivo de prueba creado: {archivo_prueba}")
    
    # Subir a Drive
    try:
        resultado = subir_archivo_rapido(
            ruta_archivo=archivo_prueba,
            nombre_drive="DogeHoot_Test.txt",
            credentials_file='../credentials.json'
        )
        
        if resultado['success']:
            print("✅ ÉXITO!")
            print(f"   📋 Archivo: {resultado['file_name']}")
            print(f"   🆔 ID: {resultado['file_id']}")
            print(f"   🔗 Ver en Drive: {resultado['web_view_link']}")
            
            # Limpiar archivo de prueba
            os.remove(archivo_prueba)
            print(f"\n🗑️  Archivo local eliminado: {archivo_prueba}")
        else:
            print(f"❌ ERROR: {resultado['message']}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
    
    print("="*60 + "\n")


def probar_subida_excel():
    """Prueba subida de archivo Excel"""
    print("\n" + "="*60)
    print("📊 PRUEBA 2: Subida de Archivo Excel")
    print("="*60)
    
    try:
        from openpyxl import Workbook
        
        # Crear Excel de prueba
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte DogeHoot"
        
        # Agregar datos
        ws['A1'] = "ID"
        ws['B1'] = "Jugador"
        ws['C1'] = "Puntuación"
        ws['A2'] = 1
        ws['B2'] = "Jugador 1"
        ws['C2'] = 100
        ws['A3'] = 2
        ws['B3'] = "Jugador 2"
        ws['C3'] = 85
        
        archivo_excel = "reporte_prueba_dogehoot.xlsx"
        wb.save(archivo_excel)
        print(f"📊 Archivo Excel creado: {archivo_excel}")
        
        # Subir a Drive
        uploader = GoogleDriveUploader(credentials_file='../credentials.json')
        resultado = uploader.subir_archivo(
            ruta_archivo=archivo_excel,
            nombre_drive="DogeHoot_Reporte_Prueba.xlsx"
        )
        
        if resultado['success']:
            print("✅ ÉXITO!")
            print(f"   📋 Archivo: {resultado['file_name']}")
            print(f"   🆔 ID: {resultado['file_id']}")
            print(f"   🔗 Ver en Drive: {resultado['web_view_link']}")
            
            # Limpiar
            os.remove(archivo_excel)
            print(f"\n🗑️  Archivo local eliminado: {archivo_excel}")
        else:
            print(f"❌ ERROR: {resultado['message']}")
            
    except ImportError:
        print("❌ ERROR: Instala openpyxl con: pip install openpyxl")
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
    
    print("="*60 + "\n")


def probar_crear_carpeta():
    """Prueba creación de carpeta"""
    print("\n" + "="*60)
    print("📁 PRUEBA 3: Crear Carpeta en Drive")
    print("="*60)
    
    try:
        uploader = GoogleDriveUploader(credentials_file='../credentials.json')
        resultado = uploader.crear_carpeta("DogeHoot Reportes")
        
        if resultado['success']:
            print("✅ ÉXITO!")
            print(f"   📁 Carpeta: {resultado['folder_name']}")
            print(f"   🆔 ID: {resultado['folder_id']}")
            print(f"   🔗 Ver en Drive: {resultado['web_view_link']}")
            return resultado['folder_id']
        else:
            print(f"❌ ERROR: {resultado['message']}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
        return None
    
    print("="*60 + "\n")


def probar_listar_archivos():
    """Prueba listar archivos"""
    print("\n" + "="*60)
    print("📋 PRUEBA 4: Listar Archivos en Drive")
    print("="*60)
    
    try:
        uploader = GoogleDriveUploader(credentials_file='../credentials.json')
        resultado = uploader.listar_archivos(max_resultados=5)
        
        if resultado['success']:
            print(f"✅ {resultado['message']}\n")
            
            if resultado['files']:
                for i, archivo in enumerate(resultado['files'], 1):
                    print(f"{i}. 📄 {archivo['name']}")
                    print(f"   🆔 ID: {archivo['id']}")
                    print(f"   📅 Creado: {archivo.get('createdTime', 'N/A')}")
                    print(f"   🔗 Link: {archivo.get('webViewLink', 'N/A')}")
                    print()
            else:
                print("   (No hay archivos)")
        else:
            print(f"❌ ERROR: {resultado['message']}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
    
    print("="*60 + "\n")


def menu_principal():
    """Menú principal de pruebas"""
    print("\n" + "="*60)
    print("🐕 DOGEHOOT - PRUEBA DE GOOGLE DRIVE UPLOADER")
    print("="*60)
    print("\nSelecciona una opción:")
    print("1. Probar subida básica de archivo")
    print("2. Probar subida de archivo Excel")
    print("3. Crear carpeta en Drive")
    print("4. Listar archivos en Drive")
    print("5. Ejecutar todas las pruebas")
    print("0. Salir")
    print("="*60)
    
    opcion = input("\n👉 Opción: ").strip()
    
    if opcion == '1':
        probar_subida_basica()
    elif opcion == '2':
        probar_subida_excel()
    elif opcion == '3':
        probar_crear_carpeta()
    elif opcion == '4':
        probar_listar_archivos()
    elif opcion == '5':
        probar_subida_basica()
        probar_subida_excel()
        probar_crear_carpeta()
        probar_listar_archivos()
    elif opcion == '0':
        print("\n👋 ¡Hasta luego!\n")
        return False
    else:
        print("\n❌ Opción inválida")
    
    return True


if __name__ == "__main__":
    print("\n🎮 IMPORTANTE:")
    print("   1. Asegúrate de tener credentials.json en la carpeta mysite/")
    print("   2. La primera vez se abrirá un navegador para autenticarte")
    print("   3. Se creará un archivo token_drive.json con tus credenciales")
    print()
    
    continuar = True
    while continuar:
        continuar = menu_principal()
