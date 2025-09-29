import os
import sys
import pandas as pd
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.preparation.data_loader import load_and_filter_daily_files
from src.detection.detectors import (
    detect_duplicated_and_failed_files, detect_unexpected_empty_files,
    detect_missing_files, detect_unexpected_volume_variation,
    detect_file_upload_after_schedule, detect_upload_of_previous_file
)

OUTPUT_DIR = "outputs"

def main(operation_date_str: str):
    """
    Orquesta la detección de incidencias para una fecha de operación específica.
    """
    CV_DATA_PATH = os.path.join(OUTPUT_DIR, "cv_data.json")
    print(f"--- [DETECCIÓN] Iniciando para el día: {operation_date_str} ---")

    print("[1/3] Cargando datos...")
    df_files_operation_date = load_and_filter_daily_files(operation_date_str)
    try:
        with open(CV_DATA_PATH, 'r') as f: cv_data = json.load(f)
    except FileNotFoundError:
        print(f"!! ERROR: No se encontró '{CV_DATA_PATH}'. Ejecuta el data miner primero.")
        return

    print("[2/3] Ejecutando detectores para cada fuente...")
    all_source_ids = [str(item.get('source_id')) for item in cv_data]
    all_incidents = []

    for source_id in all_source_ids:
        print(f"--- Analizando Fuente: {source_id} ---")
        df_source_files = df_files_operation_date[df_files_operation_date['source_id'] == source_id].copy()
        source_cv_info = next((item for item in cv_data if str(item.get('source_id')) == source_id), None)
        
        detectors = [
            detect_duplicated_and_failed_files, detect_unexpected_empty_files,
            detect_missing_files, detect_unexpected_volume_variation,
            detect_file_upload_after_schedule, detect_upload_of_previous_file,
        ]
        for detector_func in detectors:
            args = [df_source_files]
            if "source_cv_info" in detector_func.__code__.co_varnames: args.append(source_cv_info)
            if "operation_date_str" in detector_func.__code__.co_varnames: args.append(operation_date_str)
            incidents = detector_func(*args, verbose=False) # verbose=False para un log más limpio en el pipeline
            if incidents:
                all_incidents.extend(incidents)

    print("[3/3] Consolidando y guardando reporte de incidencias...")
    if not all_incidents:
        print("¡Excelente! No se encontraron incidencias.")
        # Creamos un archivo vacío para que el siguiente paso no falle
        output_path = os.path.join(OUTPUT_DIR, f"{operation_date_str}_incidents_report.json")
        with open(output_path, 'w') as f: json.dump([], f)
        return
    
    output_path = os.path.join(OUTPUT_DIR, f"{operation_date_str}_incidents_report.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_incidents, f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte de {len(all_incidents)} incidencias guardado en: {output_path}")

if __name__ == '__main__':
    # Esto solo se ejecuta si corres este script directamente para probarlo
    main(operation_date_str="2025-09-08")