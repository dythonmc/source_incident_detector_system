import pandas as pd
from datetime import datetime, timedelta
import re

def detect_duplicated_and_failed_files(df_source_files: pd.DataFrame, verbose: bool = True) -> list:
    """Detects duplicated or failed files."""
    if df_source_files is None or df_source_files.empty:
        return []
    incident_mask = (df_source_files['is_duplicated'] == True) | (df_source_files['status'].str.lower() == 'stopped')
    df_incidents = df_source_files[incident_mask]
    if verbose and df_incidents.empty:
        print("     -> [LOG] No se encontraron archivos marcados como 'is_duplicated' o con estado 'stopped'.")
        return []
    if not df_incidents.empty:
        incident_object = {
            "source_id": str(df_incidents.iloc[0]['source_id']),
            "incident_type": "Archivo Duplicado o Fallido",
            "incident_details": f"Se encontraron {len(df_incidents)} archivos marcados como duplicados o con estado 'stopped'.",
            "total_incidentes": len(df_incidents),
            "files_to_review": df_incidents['filename'].tolist()
        }
        return [incident_object]
    return []

def detect_unexpected_empty_files(df_source_files: pd.DataFrame, source_cv_info: dict, operation_date_str: str, verbose: bool = True) -> list:
    """Detects unexpected empty files based on day-of-week patterns."""
    if df_source_files is None or df_source_files.empty:
        if verbose: print("     -> [LOG] No se recibieron archivos para esta fuente hoy, no se puede verificar por archivos vacíos.")
        return []
    df_empty_files = df_source_files[df_source_files['rows'] == 0].copy()
    if df_empty_files.empty:
        if verbose: print("     -> [LOG] No se encontraron archivos con 0 filas para esta fuente hoy.")
        return []
    if not source_cv_info:
        if verbose: print("     -> [LOG] No hay datos de CV para esta fuente. Marcando archivos vacíos como incidencia por precaución.")
        incident_object = {
            "source_id": str(df_empty_files.iloc[0]['source_id']), "incident_type": "Archivo Vacío Inesperado",
            "incident_details": f"Se recibieron {len(df_empty_files)} archivos vacíos y no hay CV para verificar si es un patrón normal.",
            "total_incidentes": len(df_empty_files), "files_to_review": df_empty_files['filename'].tolist()
        }
        return [incident_object]
    today_empty_count = len(df_empty_files)
    is_incident = False
    details = ""
    operation_date = datetime.strptime(operation_date_str, '%Y-%m-%d')
    day_abbr = operation_date.strftime('%a')
    day_stats_list = source_cv_info.get("day_of_week_row_stats", [])
    day_stats = next((d for d in day_stats_list if d.get('day') == day_abbr), None)
    if day_stats and day_stats.get('empty_files_mean') is not None:
        mean_empty = day_stats['empty_files_mean']
        if today_empty_count > round(mean_empty) + 1:
            is_incident = True
            details = f"Se recibieron {today_empty_count} archivos vacíos, superando la media histórica de ~{mean_empty:.2f} para los {day_abbr}."
        elif verbose: print(f"     -> [LOG] Se encontraron {today_empty_count} archivos vacíos, lo cual es consistente con la media de {mean_empty:.2f} para los {day_abbr}.")
    else:
        if verbose: print("     -> [LOG] No se encontró 'empty_files_mean' para el día. Usando lógica de fallback (median_rows).")
        general_stats = source_cv_info.get("general_volume_stats", {})
        median_rows = general_stats.get("median_rows")
        if median_rows is not None and median_rows > 50:
            is_incident = True
            details = f"Se recibieron {today_empty_count} archivos vacíos. La mediana de filas para esta fuente es {median_rows}, por lo que no se esperan archivos vacíos."
        elif verbose:
            details_log = f"mediana de {median_rows}" if median_rows is not None else "sin datos de mediana"
            print(f"     -> [LOG] Archivos vacíos no se marcan como incidencia basado en la lógica de fallback ({details_log}).")
    if is_incident:
        incident_object = {
            "source_id": str(df_empty_files.iloc[0]['source_id']), "incident_type": "Archivo Vacío Inesperado",
            "incident_details": details, "total_incidentes": len(df_empty_files),
            "files_to_review": df_empty_files['filename'].tolist()
        }
        return [incident_object]
    return []

def detect_missing_files(df_source_files: pd.DataFrame, source_cv_info: dict, operation_date_str: str, verbose: bool = True) -> list:
    """Detects if a source sent fewer files than expected."""
    if not source_cv_info:
        if verbose: print("     -> [LOG] No hay datos de CV. No se puede verificar si faltan archivos.")
        return []
    operation_date = datetime.strptime(operation_date_str, '%Y-%m-%d')
    day_abbr = operation_date.strftime('%a')
    file_stats_list = source_cv_info.get("file_processing_daily_stats", [])
    day_stats = next((d for d in file_stats_list if d.get('day') == day_abbr), None)
    if not day_stats or day_stats.get('mean_files') is None:
        if verbose: print(f"     -> [LOG] No se encontró 'mean_files' en el CV para los {day_abbr}. No se puede verificar si faltan archivos.")
        return []
    expected_files_mean = day_stats['mean_files']
    expected_files_count = round(expected_files_mean)
    received_files_count = len(df_source_files) if df_source_files is not None else 0
    is_incident = received_files_count < expected_files_count
    if is_incident:
        details = (f"Se recibieron {received_files_count} archivos, pero se esperaban aproximadamente {expected_files_count} "
                   f"(la media histórica para los {day_abbr} es {expected_files_mean:.2f}).")
        incident_object = {
            "source_id": str(source_cv_info.get('source_id')), "incident_type": "Archivos Faltantes", "incident_details": details,
            "total_incidentes": expected_files_count - received_files_count,
            "files_to_review": df_source_files['filename'].tolist() if df_source_files is not None else []
        }
        return [incident_object]
    if verbose: print(f"     -> [LOG] Se recibieron {received_files_count} de ~{expected_files_count} archivos esperados, lo cual es aceptable.")
    return []

def detect_unexpected_volume_variation(df_source_files: pd.DataFrame, source_cv_info: dict, operation_date_str: str, verbose: bool = True) -> list:
    """Detects files with anomalous row counts compared to the daily average."""
    if df_source_files is None or df_source_files.empty: return []
    if not source_cv_info:
        if verbose: print("     -> [LOG] No hay datos de CV. No se puede verificar la variación de volumen.")
        return []
    
    operation_date = datetime.strptime(operation_date_str, '%Y-%m-%d')
    day_abbr = operation_date.strftime('%a')
    
    day_stats_list = source_cv_info.get("day_of_week_row_stats", [])
    day_stats = next((d for d in day_stats_list if d.get('day') == day_abbr), None)
    general_stats = source_cv_info.get("general_volume_stats", {})
    stdev_rows = general_stats.get("stdev_rows")

    if not day_stats or day_stats.get('rows_mean') is None or stdev_rows is None:
        if verbose: print(f"     -> [LOG] No se encontraron 'rows_mean' o 'stdev_rows' en el CV. No se puede verificar variación de volumen.")
        return []

    rows_mean = day_stats['rows_mean']
    
    # Solo aplicamos la lógica si el volumen promedio es significativo
    if rows_mean < 100:
        if verbose: print(f"     -> [LOG] La media de filas para los {day_abbr} es muy baja ({rows_mean:.2f}). Se omite la detección de variación de volumen.")
        return []

    anomalous_files = []
    for index, row in df_source_files.iterrows():
        file_rows = row['rows']
        deviation = abs(file_rows - rows_mean)
        # Regla: anómalo si se desvía en más de 2 desviaciones estándar
        is_anomalous = deviation > (2 * stdev_rows)
        
        if is_anomalous:
            anomalous_files.append(row)
        elif verbose:
            print(f"     -> [LOG] Archivo '{row['filename']}' ({file_rows} filas) está dentro del rango esperado (media: {rows_mean:.0f}, stdev: {stdev_rows:.0f}).")
            
    if anomalous_files:
        df_anomalous = pd.DataFrame(anomalous_files)
        details = (f"Se encontraron {len(df_anomalous)} archivos con un número de filas anómalo. "
                   f"La media esperada para los {day_abbr} es ~{rows_mean:.0f} (stdev: {stdev_rows:.0f}).")
        incident_object = {
            "source_id": str(source_cv_info.get('source_id')), "incident_type": "Variación de Volumen Inesperada",
            "incident_details": details, "total_incidentes": len(df_anomalous),
            "files_to_review": df_anomalous['filename'].tolist()
        }
        return [incident_object]
    
    return []

def detect_file_upload_after_schedule(df_source_files: pd.DataFrame, source_cv_info: dict, operation_date_str: str, verbose: bool = True) -> list:
    """Detects files uploaded significantly after the expected time window."""
    if df_source_files is None or df_source_files.empty: return []
    if not source_cv_info: return []
    
    operation_date = datetime.strptime(operation_date_str, '%Y-%m-%d').date()
    day_abbr = operation_date.strftime('%a')
    
    schedule_stats_list = source_cv_info.get("upload_schedule_daily_stats", [])
    day_schedule = next((d for d in schedule_stats_list if d.get('day') == day_abbr), None)
    
    if not day_schedule or not day_schedule.get('upload_window_expected_utc'):
        if verbose: print(f"     -> [LOG] No se encontró ventana de subida en el CV para los {day_abbr}.")
        return []
        
    try:
        # Extraer la hora de fin de la ventana, ej: "11:00:00–11:30:00 UTC" -> "11:30:00"
        time_window_str = day_schedule['upload_window_expected_utc']
        end_time_str = time_window_str.split('–')[1].replace(' UTC', '')
        expected_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
        deadline = datetime.combine(operation_date, expected_time) + timedelta(hours=4)
    except (IndexError, ValueError):
        if verbose: print(f"     -> [LOG] Formato de ventana de subida ('{time_window_str}') no reconocido.")
        return []

    late_files = []
    # Asegurarse de que uploaded_at es timezone-aware para la comparación
    df_source_files['uploaded_at'] = pd.to_datetime(df_source_files['uploaded_at']).dt.tz_localize(None)

    for index, row in df_source_files.iterrows():
        if row['uploaded_at'] > deadline:
            late_files.append(row)
        
    if late_files:
        df_late = pd.DataFrame(late_files)
        details = f"Se recibieron {len(df_late)} archivos más de 4 horas después del cierre de la ventana esperada (~{expected_time.strftime('%H:%M')} UTC)."
        incident_object = {
            "source_id": str(source_cv_info.get('source_id')), "incident_type": "Advertencia: Archivo Cargado Fuera de Horario",
            "incident_details": details, "total_incidentes": len(df_late),
            "files_to_review": df_late['filename'].tolist()
        }
        return [incident_object]
    
    if verbose: print("     -> [LOG] Todos los archivos se recibieron dentro del horario esperado (+4h de margen).")
    return []

def detect_upload_of_previous_file(df_source_files: pd.DataFrame, operation_date_str: str, verbose: bool = True) -> list:
    """Detects files whose coverage date (from filename) is older than a few days."""
    if df_source_files is None or df_source_files.empty: return []

    old_files = []
    operation_date = datetime.strptime(operation_date_str, '%Y-%m-%d').date()
    
    for index, row in df_source_files.iterrows():
        # Buscar una fecha en formato YYYYMMDD en el nombre del archivo
        match = re.search(r'(\d{8})', row['filename'])
        if match:
            try:
                coverage_date = datetime.strptime(match.group(1), '%Y%m%d').date()
                # Regla: Incidencia si la fecha es de hace más de 3 días
                if (operation_date - coverage_date).days > 3:
                    old_files.append(row)
            except ValueError:
                continue # No es una fecha válida, lo ignoramos

    if old_files:
        df_old = pd.DataFrame(old_files)
        details = f"Se encontraron {len(df_old)} archivos cuya fecha en el nombre es de hace más de 3 días, indicando una posible carga histórica."
        incident_object = {
            "source_id": str(df_old.iloc[0]['source_id']), "incident_type": "Advertencia: Carga de Archivo Antiguo",
            "incident_details": details, "total_incidentes": len(df_old),
            "files_to_review": df_old['filename'].tolist()
        }
        return [incident_object]
        
    if verbose: print("     -> [LOG] Todos los archivos tienen fechas de cobertura recientes en sus nombres.")
    return []