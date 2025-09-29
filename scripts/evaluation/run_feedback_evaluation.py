import os
import sys
import json
import asyncio
import re
from datetime import datetime, timezone

# Añadimos la ruta raíz del proyecto al sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from src.agents.feedback_evaluator_agent.agent import feedback_evaluator_agent

# --- CONFIGURACIÓN ---
OPERATION_DATE = "2025-09-08"
SYSTEM_INCIDENTS_PATH = f"outputs/{OPERATION_DATE}_incidents_report.json"
HUMAN_FEEDBACK_PATH = "data/Feedback - week 9 sept.xlsx"
# --- NUEVA RUTA PARA EL LOG ---
EVALUATION_LOG_PATH = "evaluation/feedback_evaluator/evaluation_results/evaluation_log.json"

APP_NAME = "feedback_eval_app"
USER_ID = "eval_user"

async def main():
    """
    Orquesta la evaluación del sistema, llama al agente y guarda su análisis en un log JSON.
    """
    print("--- Iniciando Evaluación con Agente (con Tool) vs. Feedback Humano ---")
    
    # --- 1. CARGAR LAS INCIDENCIAS DEL SISTEMA ---
    print("\n[1/4] Cargando incidencias generadas por el sistema...")
    try:
        with open(SYSTEM_INCIDENTS_PATH, 'r') as f:
            system_incidents = json.load(f)
        print(f"✓ Se cargaron {len(system_incidents)} tipos de incidencias del sistema.")
    except FileNotFoundError:
        print(f"!! ERROR: No se encontró el reporte '{SYSTEM_INCIDENTS_PATH}'")
        return

    # --- 2. EJECUTAR EL AGENTE EVALUADOR DE FEEDBACK ---
    print("\n[2/4] Ejecutando el FeedbackEvaluatorAgent...")
    runner = Runner(agent=feedback_evaluator_agent, app_name=APP_NAME, session_service=InMemorySessionService())
    session_id = f"eval_session_{OPERATION_DATE}"
    await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    
    user_prompt = f"""
    Evalúa la calidad de la detección para la fecha {OPERATION_DATE}.
    1. Usa tu herramienta `parse_feedback_excel_file` con la ruta: '{HUMAN_FEEDBACK_PATH}'.
    2. Compara el resultado con estas incidencias del sistema:
    ```json
    {json.dumps(system_incidents, indent=2)}
    ```
    3. Genera el plan de acción de mejora.
    """
    
    user_message = types.Content(role='user', parts=[types.Part(text=user_prompt)])
    final_response_str = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
            final_response_str = event.content.parts[0].text.strip()
            
    print("✓ El Agente de Evaluación de Feedback ha finalizado su análisis.")

    # --- 3. MOSTRAR Y PREPARAR EL LOG ---
    print("\n[3/4] Plan de Acción de Mejora generado por el Agente:")
    print("=====================================================")
    action_plan = {}
    try:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', final_response_str, re.DOTALL)
        if json_match:
            action_plan = json.loads(json_match.group(1))
            for i, action in enumerate(action_plan.get("action_plan", []), 1):
                print(f"{i}. {action}")
        else:
             print(final_response_str)
    except (json.JSONDecodeError, AttributeError):
        print("!! El agente no devolvió un plan de acción en el formato JSON esperado.")
    print("=====================================================")

    # --- 4. GUARDAR EL LOG DE LA EVALUACIÓN ---
    print("\n[4/4] Guardando el log de la evaluación en un archivo JSON...")
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agent_evaluated": "FeedbackEvaluatorAgent",
        "operation_date": OPERATION_DATE,
        "agent_action_plan": action_plan.get("action_plan", ["Respuesta no válida del agente."]),
        "raw_agent_response": final_response_str
    }
    try:
        os.makedirs(os.path.dirname(EVALUATION_LOG_PATH), exist_ok=True)
        all_logs = []
        if os.path.exists(EVALUATION_LOG_PATH):
            with open(EVALUATION_LOG_PATH, 'r', encoding='utf-8') as f:
                all_logs = json.load(f)
        all_logs.append(log_entry)
        with open(EVALUATION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=4)
        print(f"✓ Log de evaluación guardado exitosamente en '{EVALUATION_LOG_PATH}'")
    except Exception as e:
        print(f"!! ERROR al guardar el log de evaluación: {e}")

if __name__ == '__main__':
    asyncio.run(main())