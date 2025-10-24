import pymysql
import pymysql.cursors
import certifi

# DB_HOST = "gateway01.us-east-1.prod.aws.tidbcloud.com"
# DB_PORT = 4000
# DB_USER = "5motzQDVbZ3rA5j.root"
# DB_PASS = "tfIrzBqxBLNMq8JW"
# DB_NAME = "dogehoot"

# def obtener_conexion():
#     return pymysql.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASS,
#         db=DB_NAME,
#         port=int(DB_PORT),
#         charset='utf8mb4',
#         cursorclass=pymysql.cursors.DictCursor,
#         # autocommit=True,
#         # --- 2. AÑADE ESTA LÍNEA PARA HABILITAR SSL ---
#         ssl={'ca': certifi.where()}
#     )

def obtener_conexion():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        db='daw_db_dogehoot_pame',
        cursorclass=pymysql.cursors.DictCursor
    )    
    
# def obtener_conexion():
#     return pymysql.connect(
#         host='DMailProject.mysql.pythonanywhere-services.com',
#         user='DMailProject',
#         password='Pongo123.',
#         db='DMailProject$DMail_DB',
#         cursorclass=pymysql.cursors.DictCursor
#     )
