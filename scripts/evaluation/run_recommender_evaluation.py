import os
import sys
import json
import asyncio
from datetime import datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from src.agents.recommender.agent import recommender_agent
# --- CAMBIO AQUÍ: Importamos el agente con su nuevo nombre y desde su nueva ruta ---
from src.agents.recommender_judge_agent.agent import recommender_judge_agent

# --- CONFIGURACIÓN ---
GROUND_TRUTH_PATH = "evaluation/recommender/ground_truth/ground_truth_recommender_01.json"
EVALUATION_LOG_PATH = "evaluation/recommender/evaluation_results/evaluation_log.json"
CV_DATA_PATH = "outputs/cv_data.json"

APP_NAME = "recommender_eval_app"
USER_ID = "eval_user"

async def main():
    """Evalúa el RecommenderAgent usando un JudgeAgent formal."""
    print("--- Iniciando Evaluación Cualitativa con RecommenderJudgeAgent ---")

    # --- 1. CARGAR DATOS ---
    # ... (Esta sección no cambia)
    print("\n[1/5] Cargando caso de prueba y contexto...")
    try:
        with open(GROUND_TRUTH_PATH, 'r') as f: test_case = json.load(f)
        incident_data, golden_recommendation = test_case['incident_data'], test_case['golden_recommendation']
        with open(CV_DATA_PATH, 'r') as f: cv_data = json.load(f)
        source_id = incident_data['source_id']
        source_cv_info = next((item for item in cv_data if str(item.get('source_id')) == source_id), {})
        print("✓ Caso de prueba y contexto cargados.")
    except FileNotFoundError as e:
        print(f"!! ERROR: Archivo no encontrado: {e.filename}"); return

    # --- 2. OBTENER RECOMENDACIÓN DEL AGENTE ---
    # ... (Esta sección no cambia)
    print("\n[2/5] Ejecutando el RecommenderAgent...")
    rec_session_service = InMemorySessionService()
    rec_runner = Runner(agent=recommender_agent, app_name=APP_NAME, session_service=rec_session_service)
    rec_session_id = f"session_rec_{source_id}"
    await rec_session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=rec_session_id)
    prompt_context = f"**INCIDENCIA DETECTADA:**\n```json\n{json.dumps(incident_data, indent=2)}\n```\n\n**CONTEXTO DEL CV DE LA FUENTE:**\n```json\n{json.dumps(source_cv_info, indent=2)}\n```"
    user_message = types.Content(role='user', parts=[types.Part(text=prompt_context)])
    agent_recommendation = "No se pudo generar una recomendación."
    async for event in rec_runner.run_async(user_id=USER_ID, session_id=rec_session_id, new_message=user_message):
        if event.is_final_response() and event.content: agent_recommendation = event.content.parts[0].text.strip()
    print("✓ Recomendación del agente obtenida.")

    # --- 3. EJECUTAR EL AGENTE JUEZ ---
    print("\n[3/5] Ejecutando el RecommenderJudgeAgent...")
    judge_user_prompt = f'Por favor, evalúa la siguiente recomendación de un agente. --- **1. INCIDENTE:** ```json\n{json.dumps(incident_data, indent=2)}\n``` --- **2. RECOMENDACIÓN IDEAL (EXPERTO):** "{golden_recommendation}" --- **3. RECOMENDACIÓN DEL AGENTE (A EVALUAR):** "{agent_recommendation}"'
    
    # --- CAMBIO AQUÍ: Usamos la variable con el nuevo nombre ---
    judge_runner = Runner(agent=recommender_judge_agent, app_name=APP_NAME, session_service=InMemorySessionService())
    judge_session_id = "judge_session_01"
    await judge_runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=judge_session_id)
    judge_message = types.Content(role='user', parts=[types.Part(text=judge_user_prompt)])
    judge_verdict_str = ""
    async for event in judge_runner.run_async(user_id=USER_ID, session_id=judge_session_id, new_message=judge_message):
        if event.is_final_response() and event.content: judge_verdict_str = event.content.parts[0].text.strip()
    print("✓ Veredicto del Juez recibido.")
    
    # --- 4. MOSTRAR Y PREPARAR EL LOG ---
    # ... (Esta sección no cambia)
    print("\n[4/5] Mostrando resultados de la evaluación...")
    verdict = {}
    try:
        verdict = json.loads(judge_verdict_str)
    except json.JSONDecodeError:
        print("   !! El juez no devolvió un JSON válido.")
        verdict = {"score": 0.0, "justification": f"Respuesta no válida del Juez: {judge_verdict_str}"}
    print("\n--- REPORTE DE EVALUACIÓN CUALITATIVA: RecommenderAgent ---")
    print("==========================================================")
    print(f"   - Puntuación (Score): {verdict.get('score', 'N/A')} / 5.0")
    print(f"   - Justificación: {verdict.get('justification', 'No disponible.')}")
    print("==========================================================")
    
    # --- 5. GUARDAR EL LOG JSON ---
    # ... (Esta sección no cambia)
    print("\n[5/5] Guardando resultados en el log de evaluación...")
    log_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "agent_evaluated": "RecommenderAgent",
        "test_case_id": test_case['test_case_id'], "prompt_version": "v1.0",
        "score": verdict.get('score'), "justification": verdict.get('justification'),
        "golden_recommendation": golden_recommendation, "agent_recommendation": agent_recommendation
    }
    try:
        os.makedirs(os.path.dirname(EVALUATION_LOG_PATH), exist_ok=True)
        all_logs = []
        if os.path.exists(EVALUATION_LOG_PATH):
            with open(EVALUATION_LOG_PATH, 'r', encoding='utf-8') as f: all_logs = json.load(f)
        all_logs.append(log_entry)
        with open(EVALUATION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=4, ensure_ascii=False)
        print(f"✓ Resultados guardados exitosamente en '{EVALUATION_LOG_PATH}'")
    except Exception as e:
        print(f"!! ERROR al guardar el log de evaluación: {e}")

if __name__ == '__main__':
    asyncio.run(main())