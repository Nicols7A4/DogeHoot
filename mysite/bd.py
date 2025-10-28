import pymysql
import pymysql.cursors
import certifi
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener configuración según el entorno
DB_ENVIRONMENT = os.getenv('DB_ENVIRONMENT', 'local')

def obtener_conexion():
    """
    Obtiene la conexión a la base de datos según el entorno configurado.
    Entornos disponibles: local, tidb, pythonanywhere
    """
    if DB_ENVIRONMENT == 'tidb':
        # Configuración para TiDB Cloud (Producción)
        return pymysql.connect(
            host=os.getenv('DB_HOST_TIDB'),
            user=os.getenv('DB_USER_TIDB'),
            password=os.getenv('DB_PASS_TIDB'),
            db=os.getenv('DB_NAME_TIDB'),
            port=int(os.getenv('DB_PORT_TIDB', 4000)),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ca': certifi.where()}
        )
    elif DB_ENVIRONMENT == 'pythonanywhere':
        # Configuración para PythonAnywhere
        return pymysql.connect(
            host=os.getenv('DB_HOST_PYTHONANYWHERE'),
            user=os.getenv('DB_USER_PYTHONANYWHERE'),
            password=os.getenv('DB_PASS_PYTHONANYWHERE'),
            db=os.getenv('DB_NAME_PYTHONANYWHERE'),
            cursorclass=pymysql.cursors.DictCursor
        )
    else:
        # Configuración local (por defecto)
        return pymysql.connect(
            host=os.getenv('DB_HOST_LOCAL', '127.0.0.1'),
            user=os.getenv('DB_USER_LOCAL', 'root'),
            password=os.getenv('DB_PASS_LOCAL', ''),
            db=os.getenv('DB_NAME_LOCAL', 'dogehoot'),
            cursorclass=pymysql.cursors.DictCursor
        )
