import pandas as pd
import math

datos_formulario = {
    "id_usuario_creador": 5,
    "id_categoria": 1,
    "titulo": "Cuestionario de Matemáticas (importado)",
    "descripcion": "Preguntas de aritmética básica",
    "es_publico": 1,
    "vigente": 1
}

puntaje_base_default = 1000
tiempo_default = 15

archivo_excel = 'cuestionario_plantilla.xlsx'
print(f"--- Iniciando importación de [ {archivo_excel} ] ---")

try:
    df = pd.read_excel(archivo_excel)

    print("\n[CUESTIONARIO CREADO]")
    print(f"  TITULO: {datos_formulario['titulo']}")
    print(f"  USUARIO_ID: {datos_formulario['id_usuario_creador']}")
    
    id_cuestionario_nuevo = 999 
    
    print(f"  (Asignado ID simulado: {id_cuestionario_nuevo})\n")
    print("-----------------------------------------")
    print("--- PROCESANDO PREGUNTAS Y OPCIONES ---")
    print("-----------------------------------------")

    num_pregunta_actual = 1

    for index, fila in df.iterrows():
        
        texto_pregunta = fila['pregunta']

        if pd.isna(texto_pregunta):
            print(f"(!) Fila {index + 2} omitida: La columna 'pregunta' está vacía.")
            continue
            
        print(f"\n[PREGUNTA {num_pregunta_actual}]")
        print(f"  Texto: {texto_pregunta}")
        print(f"  (Simulando INSERT en PREGUNTAS con id_cuestionario={id_cuestionario_nuevo})")

        id_pregunta_nueva = (num_pregunta_actual * 10)

        opciones_para_insertar = []

        texto_op_correcta = fila['opcion_correcta']
        if not pd.isna(texto_op_correcta):
            opciones_para_insertar.append({
                "texto": str(texto_op_correcta),
                "es_correcta": 1
            })
        else:
            print(f"(!) ERROR Fila {index + 2}: La 'opcion_correcta' (Columna B) está vacía. Pregunta omitida.")
            continue
        
        columnas_incorrectas = df.columns[2:]
        
        for nombre_columna in columnas_incorrectas:
            texto_op_incorrecta = fila[nombre_columna]
            
            if not pd.isna(texto_op_incorrecta):
                opciones_para_insertar.append({
                    "texto": str(texto_op_incorrecta),
                    "es_correcta": 0
                })

        print(f"  Opciones a insertar (para id_pregunta={id_pregunta_nueva}):")
        
        for opc in opciones_para_insertar:
            print(f"    -> {opc['texto']} (Correcta: {opc['es_correcta']})")

        num_pregunta_actual += 1

    print("\n--- Importación local finalizada ---")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{archivo_excel}'.")
except Exception as e:
    print(f"Ha ocurrido un error inesperado: {e}")