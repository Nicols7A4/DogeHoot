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
    NO GUARDA EN BD - solo devuelve preguntas formateadas en JSON.
    El frontend las cargará en memoria y el usuario decidirá cuándo guardar.
    """
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

        # --- Validación de Encabezados (NUEVO FORMATO) ---
        headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1]] # Limpiar encabezados
        if not headers or headers[0] == "":
             return jsonify({'success': False, 'error': "La primera fila (encabezados) del Excel está vacía o es inválida."}), 400
        
        # Validar que existan las columnas del nuevo formato
        if 'pregunta' not in headers or 'opcion_c_orrecta' not in headers or 'tiempo_segundos' not in headers:
            return jsonify({'success': False, 'error': "El archivo Excel debe tener las columnas 'pregunta', 'opcion_c_orrecta' y 'tiempo_segundos'."}), 400

        # --- Encontrar índices de columnas (NUEVO FORMATO) ---
        try:
            idx_pregunta = headers.index('pregunta')
            idx_indice_correcta = headers.index('opcion_c_orrecta')  # Esta columna ahora contiene el número (1-4)
            idx_tiempo_segundos = headers.index('tiempo_segundos')  # Nueva columna obligatoria
            
            # Buscar las columnas opcion_1, opcion_2, opcion_3, opcion_4
            idx_opciones = []
            for i in range(1, 5):
                col_name = f'opcion_{i}'
                if col_name in headers:
                    idx_opciones.append(headers.index(col_name))
                else:
                    return jsonify({'success': False, 'error': f"Falta la columna '{col_name}' en el Excel."}), 400
            
            # Buscar la columna 'url_imagen'. Es opcional.
            idx_url_imagen = -1
            if 'url_imagen' in headers:
                idx_url_imagen = headers.index('url_imagen')
                
        except ValueError as ve:
             return jsonify({'success': False, 'error': f"Error al leer los encabezados: {ve}"}), 400

        # --- Procesamiento SIN GUARDAR EN BD (solo formatear JSON) ---
        preguntas_formateadas = []
        
        try:
            for row_index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if all(cell is None for cell in row):
                    continue

                # Obtener texto de la pregunta
                texto_pregunta = str(row[idx_pregunta]).strip() if row[idx_pregunta] is not None else ""
                
                # Obtener el índice de la opción correcta (1, 2, 3 o 4)
                indice_correcta_raw = row[idx_indice_correcta]
                
                # Obtener tiempo en segundos
                tiempo_segundos_raw = row[idx_tiempo_segundos]
                
                if not texto_pregunta:
                    print(f"Omitiendo fila {row_index}: Pregunta vacía.")
                    continue
                
                # Validar tiempo_segundos
                try:
                    tiempo_segundos = int(tiempo_segundos_raw) if tiempo_segundos_raw is not None else 15
                    if tiempo_segundos < 10 or tiempo_segundos > 100:
                        return jsonify({'success': False, 'error': f"Fila {row_index}: El tiempo debe estar entre 10 y 100 segundos (recibido: {tiempo_segundos})."}), 400
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'error': f"Fila {row_index}: Tiempo inválido ({tiempo_segundos_raw}). Debe ser un número entre 10 y 100."}), 400
                
                # Validar que el índice de opción correcta sea válido
                try:
                    indice_correcta = int(indice_correcta_raw) if indice_correcta_raw is not None else 0
                    if indice_correcta < 1 or indice_correcta > 4:
                        raise ValueError(f"El índice de opción correcta debe ser entre 1 y 4, recibido: {indice_correcta}")
                except (ValueError, TypeError) as e:
                    print(f"Omitiendo fila {row_index}: Índice de opción correcta inválido ({indice_correcta_raw}). {e}")
                    continue
                
                # Obtener las 4 opciones
                opciones = []
                for i, idx_op in enumerate(idx_opciones, start=1):
                    texto_opcion = str(row[idx_op]).strip() if idx_op < len(row) and row[idx_op] is not None else ""
                    if texto_opcion:
                        opciones.append({
                            'opcion': texto_opcion,
                            'es_correcta_bool': (i == indice_correcta),
                            'descripcion': None,
                            'adjunto': None
                        })
                
                # Validar que la opción marcada como correcta exista y no esté vacía
                opciones_validas = [op for op in opciones if op['opcion']]
                if indice_correcta > len(opciones_validas):
                    print(f"Omitiendo fila {row_index}: La opción correcta (índice {indice_correcta}) está vacía.")
                    continue
                
                # Validar que haya al menos 2 opciones (1 correcta + 1 incorrecta)
                if len(opciones) < 2:
                    print(f"Omitiendo fila {row_index}: Se necesitan al menos 2 opciones (1 correcta y 1 incorrecta).")
                    continue

                # Obtener la URL de la imagen (si existe)
                url_imagen = None
                if idx_url_imagen != -1 and idx_url_imagen < len(row):
                    url_imagen_val = row[idx_url_imagen]
                    if url_imagen_val and str(url_imagen_val).strip():
                        url_imagen_str = str(url_imagen_val).strip()
                        # Validar que sea una URL o dejarlo como está
                        if url_imagen_str.startswith('http'):
                            url_imagen = url_imagen_str

                # Formatear pregunta (NO GUARDAR, solo crear objeto JSON)
                pregunta_obj = {
                    # NO incluir id_pregunta (será asignado al guardar)
                    'num_pregunta': len(preguntas_formateadas) + 1,
                    'pregunta': texto_pregunta,
                    'puntaje_base': 1000,  # Valor por defecto
                    'tiempo': tiempo_segundos,
                    'adjunto': url_imagen,
                    'opciones': opciones
                }
                
                preguntas_formateadas.append(pregunta_obj)
            
            if len(preguntas_formateadas) == 0:
                return jsonify({'success': False, 'error': "El archivo Excel no contenía preguntas válidas para importar."}), 400

            # Devolver preguntas formateadas SIN GUARDAR EN BD
            return jsonify({
                'success': True,
                'message': f'{len(preguntas_formateadas)} preguntas importadas y listas para guardar.',
                'preguntas_actualizadas': preguntas_formateadas
            })

        except Exception as e:
            print(f"Error al procesar Excel (Fila {row_index}): {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Error al procesar el archivo en fila {row_index}: {e}'}), 500

    except Exception as e:
        print(f"Error general en AJAX: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Ocurrió un error inesperado en el servidor.'}), 500