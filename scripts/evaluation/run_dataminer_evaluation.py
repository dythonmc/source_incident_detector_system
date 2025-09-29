import os

import json
import asyncio
import re
from datetime import datetime, timezone
import pandas as pd



from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from src.agents.data_miner.agent import data_miner_agent

# --- RUTAS ACTUALIZADAS ---
CV_TO_TEST = "207936_native.md"
CV_FOLDER_PATH = "data/datasource_cvs"
GROUND_TRUTH_PATH = f"evaluation/data_miner/ground_truth/ground_truth_cv_{CV_TO_TEST.split('_')[0]}.json"
EVALUATION_LOG_PATH = "evaluation/data_miner/evaluation_results/evaluation_log.json"

APP_NAME = "evaluator_app"
USER_ID = "eval_user"


def compare_jsons(truth: dict, prediction: dict) -> dict:
    """Compara dos diccionarios (JSONs) y calcula métricas de precisión y completitud."""
    # (Esta función no necesita cambios)
    total_fields, correct_fields, missing_fields, mismatched_fields = 0, 0, [], []
    for key, truth_value in truth.items():
        if isinstance(truth_value, dict):
            pred_value = prediction.get(key, {})
            if not isinstance(pred_value, dict):
                mismatched_fields.append({'field': key, 'expected': 'dict', 'got': type(pred_value)})
                continue
            nested_results = compare_jsons(truth_value, pred_value)
            total_fields += nested_results['total_fields']
            correct_fields += nested_results['correct_fields']
            for item in nested_results['missing_fields']: missing_fields.append({'field': f"{key}.{item['field']}"})
            for item in nested_results['mismatched_fields']: mismatched_fields.append({'field': f"{key}.{item['field']}", 'expected': item['expected'], 'got': item['got']})
        elif isinstance(truth_value, list):
            total_fields += 1
            if key not in prediction:
                missing_fields.append({'field': key})
            elif sorted(map(str, truth_value)) == sorted(map(str, prediction.get(key, []))):
                correct_fields += 1
            else:
                mismatched_fields.append({'field': key, 'expected': truth_value, 'got': prediction.get(key)})
        else:
            total_fields += 1
            if key not in prediction:
                missing_fields.append({'field': key})
            elif str(truth_value) == str(prediction.get(key)):
                correct_fields += 1
            else:
                mismatched_fields.append({'field': key, 'expected': truth_value, 'got': prediction.get(key)})
    accuracy = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
    completeness = ((total_fields - len(missing_fields)) / total_fields) * 100 if total_fields > 0 else 0
    return {
        "total_fields": total_fields, "correct_fields": correct_fields, "missing_fields": missing_fields,
        "mismatched_fields": mismatched_fields, "accuracy_score": f"{accuracy:.2f}%", "completeness_score": f"{completeness:.2f}%"
    }

async def main():
    """Script principal para la evaluación unitaria del DataMinerAgent."""
    # (Las primeras 3 fases del main se mantienen igual)
    # ...
    print(f"--- Iniciando Evaluación para el Agente: DataMinerAgent ---")
    print(f"--- Archivo de Prueba: {CV_TO_TEST} ---")

    # --- 1. OBTENER LA PREDICCIÓN DEL AGENTE ---
    print("\n[1/4] Ejecutando el DataMinerAgent para obtener la predicción...")
    session_service = InMemorySessionService()
    runner = Runner(agent=data_miner_agent, app_name=APP_NAME, session_service=session_service)
    file_path = os.path.join(CV_FOLDER_PATH, CV_TO_TEST)
    session_id = f"eval_{CV_TO_TEST.split('_')[0]}"
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    user_prompt = f"Por favor, lee el archivo usando la herramienta read_file_content con la ruta '{file_path}' y extrae la información estructurada."
    user_message = types.Content(role='user', parts=[types.Part(text=user_prompt)])
    predicted_json = None
    try:
        final_response_text = None
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=user_message):
            if event.is_final_response() and event.content: final_response_text = event.content.parts[0].text.strip()
        if final_response_text:
            clean_json_str = re.search(r'```json\s*(\{.*?\})\s*```', final_response_text, re.DOTALL)
            if clean_json_str:
                predicted_json = json.loads(clean_json_str.group(1))
                print("✓ Predicción del agente obtenida y parseada correctamente.")
    except Exception as e:
        print(f"!! ERROR al ejecutar el agente: {e}")
        return
    if not predicted_json:
        print("!! ERROR: El agente no devolvió un JSON válido.")
        return

    # --- 2. CARGAR EL GROUND TRUTH ---
    print("\n[2/4] Cargando el archivo de Ground Truth...")
    try:
        with open(GROUND_TRUTH_PATH, 'r') as f: ground_truth_json = json.load(f)
        print(f"✓ Ground Truth cargado desde '{GROUND_TRUTH_PATH}'.")
    except FileNotFoundError:
        print(f"!! ERROR: No se encontró el archivo de Ground Truth en '{GROUND_TRUTH_PATH}'")
        return

    # --- 3. COMPARAR Y MOSTRAR RESULTADOS ---
    print("\n[3/4] Comparando predicción con Ground Truth y generando reporte...")
    results = compare_jsons(ground_truth_json, predicted_json)
    print("\n--- REPORTE DE EVALUACIÓN: DataMinerAgent ---")
    print("============================================")
    print(f"  Precisión de Campos (Accuracy): {results['accuracy_score']}")
    print(f"  Completitud de Campos (Completeness): {results['completeness_score']}")
    print("--------------------------------------------")
    if results['missing_fields']:
        print("\nCampos Faltantes en la Predicción:")
        for item in results['missing_fields']: print(f"  - {item['field']}")
    if results['mismatched_fields']:
        print("\nCampos con Valores Incorrectos:")
        for item in results['mismatched_fields']:
            print(f"  - Campo: {item['field']}")
            print(f"    - Esperado: {item['expected']}")
            print(f"    - Recibido:   {item['got']}")
    if not results['missing_fields'] and not results['mismatched_fields']:
        print("\n¡Felicitaciones! La salida del agente coincide perfectamente con el Ground Truth.")
    print("\n============================================")
    
    # --- 4. REGISTRAR LOS RESULTADOS EN EL LOG (VERSIÓN JSON) ---
    print("\n[4/4] Guardando resultados en el log de evaluación JSON...")
    
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "agent_evaluated": "DataMinerAgent",
        "test_case": CV_TO_TEST, "accuracy_score": results['accuracy_score'],
        "completeness_score": results['completeness_score'], "mismatched_count": len(results['mismatched_fields']),
        "missing_count": len(results['missing_fields']), "prompt_version": "v1.0"
    }
    
    try:
        # Leemos el log existente o creamos una lista nueva si no existe
        all_logs = []
        if os.path.exists(EVALUATION_LOG_PATH):
            with open(EVALUATION_LOG_PATH, 'r', encoding='utf-8') as f:
                all_logs = json.load(f)
        
        # Añadimos la nueva entrada y guardamos la lista completa
        all_logs.append(log_entry)
        
        with open(EVALUATION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=4, ensure_ascii=False)
            
        print(f"✓ Resultados guardados exitosamente en '{EVALUATION_LOG_PATH}'")
        
    except Exception as e:
        print(f"!! ERROR al guardar el log de evaluación: {e}")


if __name__ == '__main__':
    asyncio.run(main())