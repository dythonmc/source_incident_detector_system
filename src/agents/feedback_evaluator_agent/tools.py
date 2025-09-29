import pandas as pd
import re
from typing import Dict
from google.adk.tools import FunctionTool

def parse_feedback_excel_file(feedback_file_path: str) -> Dict:
    """
    Lee un archivo Excel (XLSX) de feedback humano, lo parsea para extraer
    incidencias estructuradas y devuelve un JSON limpio.

    Args:
        feedback_file_path (str): La ruta al archivo de feedback en formato .xlsx.

    Returns:
        Un diccionario indicando el resultado.
        En éxito, 'status' es 'success' y contiene 'parsed_feedback'.
        En error, 'status' es 'error' y contiene 'error_message'.
    """
    try:
        # --- CAMBIO CLAVE: Usamos read_excel para el archivo .xlsx ---
        df_feedback = pd.read_excel(feedback_file_path, engine='openpyxl')
    except FileNotFoundError:
        return {"status": "error", "error_message": f"Archivo no encontrado en: {feedback_file_path}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Error al leer el archivo Excel: {e}"}

    structured_feedback = []
    pattern = re.compile(
        r"(\*.*?)\s*\(id:\s*(\d+)\)\s*\*.*?\s*–\s*(\d{4}-\d{2}-\d{2}):\s*(.*?)(?=\s*→\s*\*Action:|$)\s*(→\s*\*Action:.*)?"
    )

    for index, row in df_feedback.dropna(subset=['Report']).iterrows():
        report_date = row['Date']
        for line in str(row['Report']).split('\n'):
            match = pattern.search(line)
            if match:
                source_name = match.group(1).strip().replace('*', '').strip()
                source_id = match.group(2).strip()
                incident_date = match.group(3).strip()
                insight = match.group(4).strip()
                action_raw = match.group(5) if match.group(5) else ""
                action = action_raw.replace('→ *Action:*', '').strip()
                structured_feedback.append({
                    "report_date": report_date, "source_name": source_name, "source_id": source_id,
                    "incident_date": incident_date, "insight": insight, "human_action": action
                })
    
    if structured_feedback:
        return {"status": "success", "parsed_feedback": structured_feedback}
    
    return {"status": "error", "error_message": "No se pudo parsear ninguna entrada del archivo de feedback."}

# --- Creación Formal de la Herramienta ---
parse_feedback_tool = FunctionTool(func=parse_feedback_excel_file)