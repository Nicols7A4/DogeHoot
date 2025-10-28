import openpyxl
from datetime import datetime
from flask import (
    Blueprint, request,
    redirect, url_for, send_from_directory, jsonify
)

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
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
    """
    try:
        static_dir = os.path.join(parent_dir, 'static')
        print(f"Buscando plantilla en: {static_dir}") 
        return send_from_directory(
            directory=static_dir,
            path='cuestionario_plantilla.xlsx',
            as_attachment=True
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
    Añade preguntas (CON URL DE IMAGEN) y opciones al cuestionario.
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

        # ... (otras validaciones de archivo) ...
        if not archivo or not archivo.filename.endswith('.xlsx'):
             return jsonify({'success': False, 'error': 'Archivo no válido. Solo se permite .xlsx'}), 400

        # --- Lectura con openpyxl ---
        try:
            workbook = openpyxl.load_workbook(archivo)
            sheet = workbook.active
        except Exception as e:
             print(f"Error al cargar Excel con openpyxl: {e}")
             return jsonify({'success': False, 'error': 'Error al leer el archivo Excel. Verifica que no esté corrupto o protegido.'}), 400

        # --- Validación de Encabezados ---
        headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1]] # Limpiar encabezados
        if not headers or headers[0] == "":
             return jsonify({'success': False, 'error': "La primera fila (encabezados) del Excel está vacía o es inválida."}), 400
        if 'pregunta' not in headers or 'opcion_correcta' not in headers:
            return jsonify({'success': False, 'error': "El archivo Excel debe tener las columnas 'pregunta' y 'opcion_correcta'."}), 400

        # --- Encontrar índices de columnas (incluida la de imagen) ---
        try:
            idx_pregunta = headers.index('pregunta')
            idx_op_correcta = headers.index('opcion_correcta')
            indices_op_incorrectas = [i for i, h in enumerate(headers) if h.startswith('opcion_incorrecta')]
            
            # ¡NUEVO! Busca la columna 'url_imagen'. Es opcional.
            idx_url_imagen = -1 # Valor por defecto si no se encuentra
            if 'url_imagen' in headers:
                idx_url_imagen = headers.index('url_imagen')
                
        except ValueError:
             return jsonify({'success': False, 'error': "Error al leer los encabezados requeridos."}), 400

        # --- Procesamiento en Base de Datos ---
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

                    texto_pregunta = str(row[idx_pregunta]).strip() if row[idx_pregunta] is not None else ""
                    op_correcta = str(row[idx_op_correcta]).strip() if row[idx_op_correcta] is not None else ""

                    if not texto_pregunta or not op_correcta:
                        print(f"Omitiendo fila {row_index}: Datos incompletos.")
                        continue

                    # ¡NUEVO! Obtener la URL de la imagen (si existe)
                    url_imagen = None
                    if idx_url_imagen != -1 and idx_url_imagen < len(row):
                        url_imagen_val = row[idx_url_imagen]
                        if url_imagen_val and str(url_imagen_val).strip().startswith('http'):
                            url_imagen = str(url_imagen_val).strip()

                    # --- ¡INSERT SQL ACTUALIZADO! ---
                    # Ahora incluye la columna 'adjunto'
                    sql_pregunta = """
                        INSERT INTO PREGUNTAS 
                        (id_cuestionario, pregunta, num_pregunta, puntaje_base, tiempo, adjunto) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    puntaje_base = 1000
                    tiempo = 15
                    cursor.execute(sql_pregunta, (
                        id_cuestionario, texto_pregunta, num_pregunta_siguiente, 
                        puntaje_base, tiempo, url_imagen  # <-- url_imagen se inserta aquí
                    ))
                    id_pregunta_nueva = cursor.lastrowid

                    # --- Insertar Opciones (sin cambios) ---
                    sql_opcion = "INSERT INTO OPCIONES (opcion, id_pregunta, es_correcta_bool) VALUES (%s, %s, %s)"
                    cursor.execute(sql_opcion, (op_correcta, id_pregunta_nueva, 1))

                    opciones_incorrectas_insertadas = 0
                    for idx in indices_op_incorrectas:
                        if idx < len(row):
                            op_incorrecta = str(row[idx]).strip() if row[idx] is not None else ""
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
                
                # --- Devolver lista actualizada (sin cambios) ---
                if connection:
                    connection.close()
                    connection = None 
                
                cuestionario_actualizado = cc.obtener_completo_por_id(id_cuestionario)
                lista_preguntas = cuestionario_actualizado.get('preguntas', []) if cuestionario_actualizado else []

                return jsonify({
                    'success': True,
                    'message': f'{preguntas_importadas} preguntas importadas correctamente.',
                    'preguntas_actualizadas': lista_preguntas
                })

            except ValueError as ve:
                connection.rollback()
                print(f"Error de validación en AJAX (Fila {row_index}): {ve}")
                return jsonify({'success': False, 'error': str(ve)}), 400
            except Exception as db_error:
                connection.rollback()
                print(f"Error en transacción AJAX (Fila {row_index}): {db_error}")
                return jsonify({'success': False, 'error': f'Error al procesar el archivo en fila {row_index}: {db_error}'}), 500

    except Exception as e:
        print(f"Error general en AJAX: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Ocurrió un error inesperado en el servidor.'}), 500
    finally:
        if connection:
            connection.close()