"""
SCRIPT DE PRUEBA PARA ENVÍO DE CORREOS - DogeHoot
==================================================
Este script prueba el envío de correos con Gmail y Hotmail

ANTES DE EJECUTAR:
1. Copia .env.example a .env
2. Completa tus credenciales en .env
3. Ejecuta: python test_enviar_correo.py
"""

import sys
import os

# Agregar el directorio padre al path para importar módulos
try:
    current_file = __file__
except NameError:
    # En entornos interactivos (REPL/notebook) __file__ puede no existir
    current_file = sys.argv[0] if len(sys.argv) > 0 and sys.argv[0] else os.getcwd()
sys.path.insert(0, os.path.dirname(os.path.abspath(current_file)))
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_sender_test import EmailSender
import openpyxl
from datetime import datetime


def crear_excel_prueba():
    """Crea un archivo Excel de prueba con datos ficticios"""
    print("📝 Creando archivo Excel de prueba...")
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Partidas"
    
    # Encabezados
    encabezados = ['ID Partida', 'Fecha', 'Cuestionario', 'Participantes', 'Preguntas', 'Ganador']
    ws.append(encabezados)
    
    # Datos de ejemplo
    datos = [
        [1, '2025-10-20 15:30', 'Historia Mundial', 8, 10, 'Juan Pérez'],
        [2, '2025-10-21 10:15', 'Ciencias Naturales', 12, 15, 'María López'],
        [3, '2025-10-22 18:45', 'Matemáticas', 6, 20, 'Carlos Ruiz'],
        [4, '2025-10-23 14:00', 'Geografía', 10, 12, 'Ana García'],
    ]
    
    for fila in datos:
        ws.append(fila)
    
    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    
    # Guardar archivo
    nombre_archivo = f'reporte_partidas_prueba_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    ruta_completa = os.path.join(os.path.dirname(__file__), nombre_archivo)
    wb.save(ruta_completa)
    
    print(f"✅ Archivo creado: {nombre_archivo}")
    return ruta_completa


def probar_gmail():
    """Prueba el envío de correo con Gmail"""
    print("\n" + "="*60)
    print("🔵 PRUEBA DE ENVÍO CON GMAIL")
    print("="*60)
    
    sender = EmailSender()
    
    # Verificar credenciales
    if not sender.gmail_user or not sender.gmail_password:
        print("❌ Credenciales de Gmail no configuradas en .env")
        print("Por favor configura GMAIL_USER y GMAIL_APP_PASSWORD en tu archivo .env")
        return False
    
    print(f"📧 Enviando desde: {sender.gmail_user}")
    
    # Solicitar correo destino
    destinatario = input("Ingresa el correo destino (Gmail): ").strip()
    if not destinatario:
        print("❌ Correo destino no proporcionado")
        return False
    
    # Crear Excel de prueba
    archivo_excel = crear_excel_prueba()
    
    # Enviar correo
    print(f"\n📤 Enviando correo a {destinatario}...")
    resultado = sender.enviar_reporte_excel(
        destinatario=destinatario,
        tipo_servicio='drive',
        archivo_excel=archivo_excel
    )
    
    # Mostrar resultado
    if resultado['success']:
        print(f"✅ {resultado['message']}")
        return True
    else:
        print(f"❌ {resultado['message']}")
        return False


def probar_hotmail():
    """Prueba el envío de correo con Hotmail"""
    print("\n" + "="*60)
    print("🔷 PRUEBA DE ENVÍO CON HOTMAIL/OUTLOOK")
    print("="*60)
    print("⚠️  ADVERTENCIA: En PythonAnywhere gratuito, esto probablemente falle")
    print("    debido a que Outlook SMTP está bloqueado")
    
    sender = EmailSender()
    
    # Verificar credenciales
    if not sender.hotmail_user or not sender.hotmail_password:
        print("❌ Credenciales de Hotmail no configuradas en .env")
        print("Por favor configura HOTMAIL_USER y HOTMAIL_APP_PASSWORD en tu archivo .env")
        return False
    
    print(f"📧 Enviando desde: {sender.hotmail_user}")
    
    # Solicitar correo destino
    destinatario = input("Ingresa el correo destino (Hotmail/Outlook): ").strip()
    if not destinatario:
        print("❌ Correo destino no proporcionado")
        return False
    
    # Crear Excel de prueba
    archivo_excel = crear_excel_prueba()
    
    # Enviar correo
    print(f"\n📤 Enviando correo a {destinatario}...")
    resultado = sender.enviar_reporte_excel(
        destinatario=destinatario,
        tipo_servicio='onedrive',
        archivo_excel=archivo_excel
    )
    
    # Mostrar resultado
    if resultado['success']:
        print(f"✅ {resultado['message']}")
        return True
    else:
        print(f"❌ {resultado['message']}")
        return False


def probar_correo_simple_gmail():
    """Prueba envío de correo simple sin archivo adjunto"""
    print("\n" + "="*60)
    print("📨 PRUEBA DE CORREO SIMPLE CON GMAIL (sin adjunto)")
    print("="*60)
    
    sender = EmailSender()
    
    if not sender.gmail_user or not sender.gmail_password:
        print("❌ Credenciales de Gmail no configuradas")
        return False
    
    print(f"📧 Enviando desde: {sender.gmail_user}")
    destinatario = input("Ingresa el correo destino: ").strip()
    
    if not destinatario:
        print("❌ Correo destino no proporcionado")
        return False
    
    mensaje_html = """
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #4A90E2;">🐕 Prueba de DogeHoot</h2>
            <p>¡Este es un correo de prueba!</p>
            <p>Si recibes este mensaje, significa que el sistema de envío de correos funciona correctamente.</p>
            <hr>
            <p style="color: #999; font-size: 12px;">Correo de prueba - DogeHoot</p>
        </body>
    </html>
    """
    
    print(f"📤 Enviando correo de prueba a {destinatario}...")
    resultado = sender.enviar_correo_gmail(
        destinatario=destinatario,
        asunto='🐕 Prueba de DogeHoot - Sistema de Correos',
        mensaje_html=mensaje_html
    )
    
    if resultado['success']:
        print(f"✅ {resultado['message']}")
        return True
    else:
        print(f"❌ {resultado['message']}")
        return False


def menu_principal():
    """Menú interactivo para seleccionar pruebas"""
    print("\n" + "="*60)
    print("🎮 DOGEHOOT - SISTEMA DE PRUEBAS DE CORREO")
    print("="*60)
    print("\nSelecciona una opción:")
    print("1. Probar envío simple con Gmail (sin adjunto)")
    print("2. Probar envío con Gmail + archivo Excel")
    print("3. Probar envío con Hotmail + archivo Excel")
    print("4. Ejecutar todas las pruebas")
    print("0. Salir")
    print("="*60)
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == '1':
        probar_correo_simple_gmail()
    elif opcion == '2':
        probar_gmail()
    elif opcion == '3':
        probar_hotmail()
    elif opcion == '4':
        probar_correo_simple_gmail()
        input("\nPresiona Enter para continuar con la siguiente prueba...")
        probar_gmail()
        input("\nPresiona Enter para continuar con la siguiente prueba...")
        probar_hotmail()
    elif opcion == '0':
        print("\n👋 ¡Hasta luego!")
        return
    else:
        print("\n❌ Opción inválida")
    
    # Volver al menú
    input("\n\nPresiona Enter para volver al menú...")
    menu_principal()


if __name__ == '__main__':
    try:
        # Verificar que exista el archivo .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if not os.path.exists(env_path):
            print("⚠️  ADVERTENCIA: No se encontró el archivo .env")
            print("Por favor, copia .env.example a .env y configura tus credenciales")
            print(f"Ubicación esperada: {env_path}")
            input("\nPresiona Enter para continuar de todos modos...")
        
        menu_principal()
        
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
