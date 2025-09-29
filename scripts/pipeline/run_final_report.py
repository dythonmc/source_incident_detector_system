import os
import sys
import json
import asyncio
from datetime import datetime

# Añadimos la ruta raíz del proyecto al sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Importaciones de ADK
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Importaciones de nuestros módulos
from src.agents.recommender.agent import recommender_agent
from src.reporting.consolidator import classify_source_severity

# --- CONFIGURACIÓN ---
OPERATION_DATE = "2025-09-08"
OUTPUT_DIR = "outputs"
# Archivos de entrada
INCIDENTS_REPORT_PATH = os.path.join(OUTPUT_DIR, f"{OPERATION_DATE}_incidents_report.json")
CV_DATA_PATH = os.path.join(OUTPUT_DIR, "cv_data.json")
# Archivos de salida
FINAL_REPORT_MD_PATH = os.path.join(OUTPUT_DIR, f"{OPERATION_DATE}_executive_summary.md")
FINAL_REPORT_JSON_PATH = os.path.join(OUTPUT_DIR, f"{OPERATION_DATE}_executive_summary.json") # <-- Nueva salida

# Constantes para la sesión de ADK
APP_NAME = "recommender_app"
USER_ID = "reporter_user"

def generate_markdown_report(classified_data: dict, date_str: str, output_path: str):
    """Genera un reporte legible en formato Markdown."""
    print("   -> Generando reporte en formato Markdown...")
    report_lines = []
    report_lines.append(f"# Reporte Diario de Incidencias de Procesamiento")
    report_lines.append(f"**Fecha de Análisis:** {date_str}")
    
    urgent_sources = {k: v for k, v in classified_data.items() if v['status_emoji'] == '🔴'}
    warning_sources = {k: v for k, v in classified_data.items() if v['status_emoji'] == '🟡'}

    summary = (f"Se analizaron las fuentes de datos y se encontraron **{len(urgent_sources)}** fuentes con criticidad "
               f"**URGENTE** y **{len(warning_sources)}** que **REQUIEREN ATENCIÓN**.")
    report_lines.append(f"\n## Resumen del Día\n{summary}\n")

    if urgent_sources:
        report_lines.append("---\n## 🔴 URGENTE - Acción Inmediata Requerida")
        for source_id, data in urgent_sources.items():
            report_lines.append(f"\n### Fuente: `{source_id}` (Total Incidencias: {data['total_incidents']})")
            for incident in data['incidents']:
                report_lines.append(f"- **Tipo:** {incident['incident_type']}")
                report_lines.append(f"  - **Detalle:** {incident['incident_details']}")
                report_lines.append(f"  - **Recomendación IA:** {incident.get('recommendation', 'No generada.')}")
                if incident.get('files_to_review'):
                    report_lines.append(f"  - **Archivos Afectados ({incident['total_incidentes']}):**")
                    for filename in incident['files_to_review']:
                        report_lines.append(f"    - `{filename}`")
    
    if warning_sources:
        report_lines.append("---\n## 🟡 REQUIERE ATENCIÓN - Necesita Investigación")
        for source_id, data in warning_sources.items():
            report_lines.append(f"\n### Fuente: `{source_id}` (Total Incidencias: {data['total_incidents']})")
            for incident in data['incidents']:
                report_lines.append(f"- **Tipo:** {incident['incident_type']}")
                report_lines.append(f"  - **Detalle:** {incident['incident_details']}")
                report_lines.append(f"  - **Recomendación IA:** {incident.get('recommendation', 'No generada.')}")
                if incident.get('files_to_review'):
                    report_lines.append(f"  - **Archivos Afectados ({incident['total_incidentes']}):**")
                    for filename in incident['files_to_review']:
                        report_lines.append(f"    - `{filename}`")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"✓ Reporte Markdown guardado en: {output_path}")

async def main():
    """Script principal para consolidar, enriquecer y generar el reporte final."""
    print(f"--- Iniciando Generación de Reporte Ejecutivo para el día: {OPERATION_DATE} ---")

    # --- 1. FASE DE CARGA DE DATOS ---
    print("\n[1/4] Cargando reporte de incidencias y datos de CVs...")
    try:
        with open(INCIDENTS_REPORT_PATH, 'r') as f: incidents_data = json.load(f)
        print(f"✓ Reporte de incidencias cargado: {len(incidents_data)} tipos de incidencias encontradas.")
        with open(CV_DATA_PATH, 'r') as f: cv_data = json.load(f)
        print(f"✓ Datos de inteligencia de CVs cargados.")
    except FileNotFoundError as e:
        print(f"!! ERROR: No se encontró un archivo de entrada necesario: {e.filename}")
        return

    # --- 2. FASE DE CLASIFICACIÓN DE SEVERIDAD ---
    print("\n[2/4] Clasificando la severidad para cada fuente...")
    classified_sources = classify_source_severity(incidents_data)
    print("✓ Severidad clasificada.")

    # --- 3. FASE DE ENRIQUECIMIENTO CON IA (RECOMENDACIONES) ---
    print("\n[3/4] Generando recomendaciones con el Agente de IA...")
    session_service = InMemorySessionService()
    runner = Runner(agent=recommender_agent, app_name=APP_NAME, session_service=session_service)
    
    for source_id, data in classified_sources.items():
        print(f"   -> Obteniendo recomendaciones para la fuente: {source_id}...")
        source_cv_info = next((item for item in cv_data if str(item.get('source_id')) == source_id), {})
        for incident in data['incidents']:
            session_id = f"session_rec_{source_id}_{incident['incident_type']}"
            await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
            prompt_context = f"**INCIDENCIA DETECTADA:**\n```json\n{json.dumps(incident, indent=2)}\n```\n\n**CONTEXTO DEL CV DE LA FUENTE:**\n```json\n{json.dumps(source_cv_info, indent=2)}\n```"
            user_message = types.Content(role='user', parts=[types.Part(text=prompt_context)])
            recommendation_text = "No se pudo generar una recomendación."
            async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=user_message):
                if event.is_final_response() and event.content:
                    recommendation_text = event.content.parts[0].text.strip()
            incident['recommendation'] = recommendation_text
    print("✓ Todas las recomendaciones han sido generadas.")
    
    # --- 4. FASE DE GENERACIÓN DE REPORTES FINALES ---
    print("\n[4/4] Creando los archivos de reporte finales...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # --- NUEVO: Guardar el reporte JSON enriquecido ---
    print(f"   -> Guardando reporte JSON enriquecido...")
    with open(FINAL_REPORT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(classified_sources, f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte JSON guardado en: {FINAL_REPORT_JSON_PATH}")

    # Guardar el reporte Markdown para lectura humana
    generate_markdown_report(classified_sources, OPERATION_DATE, FINAL_REPORT_MD_PATH)
    
    print("\n--- Proceso de Reporte Ejecutivo Finalizado ---")

if __name__ == '__main__':
    asyncio.run(main())