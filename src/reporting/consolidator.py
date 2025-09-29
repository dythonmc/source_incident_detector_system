# src/reporting/consolidator.py
import pandas as pd

def classify_source_severity(incidents: list) -> dict:
    """
    Toma una lista de incidencias y devuelve un diccionario con la clasificación
    de severidad y las incidencias agrupadas para cada fuente.

    Args:
        incidents (list): La lista de objetos de incidencia generada en la Fase 2.

    Returns:
        dict: Un diccionario donde las claves son los source_id y los valores
              contienen el nivel de severidad y la lista de sus incidencias.
              Ej: {'12345': {'severity': '🔴 URGENTE', 'incidents': [...]}}
    """
    if not incidents:
        return {}

    # Usamos pandas para agrupar fácilmente las incidencias por source_id
    df_incidents = pd.DataFrame(incidents)
    
    # Creamos un diccionario para almacenar el resultado final
    classified_sources = {}

    # Agrupamos por 'source_id'
    for source_id, group in df_incidents.groupby('source_id'):
        
        num_incidents = len(group)
        severity = "🟢 TODO BIEN" # Por defecto
        status_emoji = "🟢"

        # Aplicamos las reglas de criticidad
        # Por ahora, consideramos todas las incidencias como "urgentes" para la regla 1.
        if num_incidents > 3: # Más de 3 incidencias totales
            severity = "🔴 URGENTE - Acción Inmediata Requerida"
            status_emoji = "🔴"
        elif num_incidents >= 1: # Al menos una incidencia
            severity = "🟡 REQUIERE ATENCIÓN - Necesita Investigación"
            status_emoji = "🟡"
        
        # Guardamos el resultado para esta fuente
        classified_sources[source_id] = {
            "severity": severity,
            "status_emoji": status_emoji,
            "total_incidents": num_incidents,
            "incidents": group.to_dict('records') # Convertimos el grupo de nuevo a una lista de diccionarios
        }
        
    return classified_sources
    