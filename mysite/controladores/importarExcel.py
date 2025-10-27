import openpyxl
from datetime import datetime
from flask import (
    Blueprint, request,
    redirect, url_for, send_from_directory, jsonify
)

import sys
import os
# Obtiene la ruta del directorio actual (controladores)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Obtiene la ruta del directorio padre (mysite)
parent_dir = os.path.dirname(current_dir)
# Si el directorio padre no está en las rutas de búsqueda de Python, lo añade
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from bd import obtener_conexion
from . import cuestionarios as cc

importar_bp = Blueprint('importarExcel', __name__,
                        static_folder='static')


@importar_bp.route('/descargar_plantilla')
def descargar_plantilla():
    """
    Sirve el archivo de plantilla Excel para descargar.
    Busca la plantilla en la carpeta 'static' principal (fuera de 'controladores').
    """
    try:
        # Construye la ruta a la carpeta 'static' principal usando parent_dir
        static_dir = os.path.join(parent_dir, 'static')

        print(f"Buscando plantilla en: {static_dir}") # Log para verificar la ruta

        return send_from_directory(
            directory=static_dir,
            path='cuestionario_plantilla.xlsx',
            as_attachment=True # Fuerza la descarga
        )
    except FileNotFoundError:
        print(f"ERROR: Archivo 'cuestionario_plantilla.xlsx' no encontrado en '{static_dir}'.")
        return "Archivo de plantilla no encontrado en el servidor.", 404
    except Exception as e:
        print(f"Error inesperado al intentar enviar plantilla: {e}")
        return "Error interno del servidor al procesar la solicitud.", 500


@importar_bp.route('/importar-preguntas-ajax', methods=['POST'])
def importar_preguntas_ajax():
    """
    Procesa la subida de un archivo Excel vía AJAX.
    Añade las preguntas y opciones al cuestionario especificado.
    Devuelve una respuesta JSON con la lista de preguntas actualizada.
    """
    connection = None
    row_index = 1
    id_cuestionario = None
    try:
        id_cuestionario_str = request.form.get('id_cuestionario')
        archivo = request.files.get('archivo_excel')

        # --- Validaciones ---
        if not id_cuestionario_str:
            return jsonify({'success': False, 'error': 'No se proporcionó el ID del cuestionario.'}), 400
        try:
            id_cuestionario = int(id_cuestionario_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'ID de cuestionario inválido.'}), 400

        if not archivo or archivo.filename == '':
            return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo Excel.'}), 400
        if not archivo.filename.endswith('.xlsx'):
            return jsonify({'success': False, 'error': 'Archivo no válido. Solo se permite .xlsx'}), 400

        try:
            workbook = openpyxl.load_workbook(archivo)
            sheet = workbook.active
        except Exception as e:
             print(f"Error al cargar Excel con openpyxl: {e}")
             return jsonify({'success': False, 'error': 'Error al leer el archivo Excel. Verifica que no esté corrupto o protegido.'}), 400

        headers = [cell.value for cell in sheet[1]]
        if not headers or headers[0] is None:
             return jsonify({'success': False, 'error': "La primera fila (encabezados) del Excel está vacía o es inválida."}), 400
        if 'pregunta' not in headers or 'opcion_correcta' not in headers:
            return jsonify({'success': False, 'error': "El archivo Excel debe tener al menos las columnas 'pregunta' y 'opcion_correcta' en la primera fila."}), 400

        try:
            idx_pregunta = headers.index('pregunta')
            idx_op_correcta = headers.index('opcion_correcta')
            indices_op_incorrectas = [i for i, h in enumerate(headers) if h and str(h).startswith('opcion_incorrecta')]
        except ValueError:
             return jsonify({'success': False, 'error': "No se encontraron las columnas 'pregunta' u 'opcion_correcta'."}), 400

        connection = obtener_conexion()
        if not connection:
            return jsonify({'success': False, 'error': 'Error al conectar con la base de datos.'}), 500

        preguntas_importadas = 0
        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION")
            try:
                cursor.execute("SELECT MAX(num_pregunta) FROM PREGUNTAS WHERE id_cuestionario = %s", (id_cuestionario,))
                max_num = cursor.fetchone()
                num_pregunta_siguiente = (max_num['MAX(num_pregunta)'] or 0) + 1

                for row_index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if all(cell is None for cell in row):
                        continue

                    texto_pregunta = row[idx_pregunta]
                    op_correcta = row[idx_op_correcta]
                    texto_pregunta = str(texto_pregunta).strip() if texto_pregunta is not None else ""
                    op_correcta = str(op_correcta).strip() if op_correcta is not None else ""

                    if not texto_pregunta or not op_correcta:
                        print(f"Omitiendo fila {row_index}: Datos incompletos.")
                        continue

                    sql_pregunta = "INSERT INTO PREGUNTAS (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql_pregunta, (id_cuestionario, texto_pregunta, num_pregunta_siguiente, 1000, 15))
                    id_pregunta_nueva = cursor.lastrowid

                    sql_opcion = "INSERT INTO OPCIONES (opcion, id_pregunta, es_correcta_bool) VALUES (%s, %s, %s)"
                    cursor.execute(sql_opcion, (op_correcta, id_pregunta_nueva, 1))

                    opciones_incorrectas_insertadas = 0
                    for idx in indices_op_incorrectas:
                        if idx < len(row):
                            op_incorrecta = row[idx]
                            op_incorrecta = str(op_incorrecta).strip() if op_incorrecta is not None else ""
                            if op_incorrecta:
                                cursor.execute(sql_opcion, (op_incorrecta, id_pregunta_nueva, 0))
                                opciones_incorrectas_insertadas += 1

                    if opciones_incorrectas_insertadas == 0:
                         raise ValueError(f"La pregunta '{texto_pregunta}' (Fila {row_index}) debe tener al menos una opción incorrecta válida.")

                    num_pregunta_siguiente += 1
                    preguntas_importadas += 1
                
                if preguntas_importadas == 0:
                    raise ValueError("El archivo Excel no contenía preguntas válidas para importar.")

                connection.commit()

                if connection:
                    connection.close()
                    connection = None 
                
                cuestionario_actualizado = cc.obtener_completo_por_id(id_cuestionario)
                lista_preguntas = cuestionario_actualizado.get('preguntas', []) if cuestionario_actualizado else []

                return jsonify({
                    'success': True,
                    'message': f'{preguntas_importadas} preguntas importadas correctamente.',
                    'preguntas_actualizadas': lista_preguntas # ¡Devolvemos la nueva lista!
                })

            except ValueError as ve:
                connection.rollback()
                print(f"Error de validación en AJAX (Fila {row_index}): {ve}")
                return jsonify({'success': False, 'error': str(ve)}), 400
            except Exception as db_error:
                connection.rollback()
                print(f"Error en transacción AJAX (Fila {row_index}): {db_error}")
                return jsonify({'success': False, 'error': f'Error al procesar el archivo en fila {row_index}: {db_error}'}), 500

    except openpyxl.utils.exceptions.InvalidFileException:
         print("Error: El archivo subido no es un formato Excel .xlsx válido.")
         return jsonify({'success': False, 'error': 'El archivo subido no parece ser un archivo Excel .xlsx válido.'}), 400
    except Exception as e:
        print(f"Error general en AJAX: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Ocurrió un error inesperado en el servidor.'}), 500
    finally:
        if connection:
            connection.close()