import sys
import os
from datetime import datetime, timedelta

# Añadimos la ruta a 'src' para que Python encuentre nuestros módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importamos las funciones 'main' de nuestros scripts, renombrándolas para claridad
from scripts.pipeline.run_data_mining import main as run_data_mining
from scripts.pipeline.run_incident_detection import main as run_incident_detection
from scripts.pipeline.run_final_report import main as run_final_report

def run_full_pipeline():
    """
    Punto de entrada único para ejecutar el pipeline completo de detección de incidencias.
    """
    print("======================================================")
    print("===   INICIANDO PIPELINE DE DETECCIÓN DE INCIDENCIAS   ===")
    print("======================================================")

    # Determinamos la fecha de operación (ej. para hoy o el día anterior)
    # Para la prueba, usaremos una fecha fija. En producción, podría ser datetime.now()
    operation_date = datetime.strptime("2025-09-08", "%Y-%m-%d")
    date_str = operation_date.strftime('%Y-%m-%d')
    
    print(f"\nFecha de Operación Seleccionada: {date_str}\n")

    try:
        # --- FASE 1: Minería de Datos de CVs ---
        print("--- [FASE 1/3] Ejecutando Data Miner Agent... ---")
        asyncio.run(run_data_mining())
        print("--- [FASE 1/3] Data Miner Agent finalizado. ---\n")

        # --- FASE 2: Detección de Incidencias ---
        print("--- [FASE 2/3] Ejecutando Motor de Detección de Incidencias... ---")
        run_incident_detection(operation_date_str=date_str)
        print("--- [FASE 2/3] Motor de Detección finalizado. ---\n")

        # --- FASE 3: Generación de Reporte Ejecutivo ---
        print("--- [FASE 3/3] Ejecutando Generador de Reporte Ejecutivo... ---")
        asyncio.run(run_final_report(operation_date_str=date_str))
        print("--- [FASE 3/3] Generador de Reporte finalizado. ---\n")

        print("======================================================")
        print("=== PIPELINE FINALIZADO EXITOSAMENTE ===")
        print("======================================================")

    except Exception as e:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!!   ERROR CRÍTICO DURANTE LA EJECUCIÓN DEL PIPELINE: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Aquí se podrían añadir notificaciones de error (ej. enviar un email)

if __name__ == '__main__':
    # Para ejecutar el pipeline completo, solo corremos este archivo.
    # Necesitamos importar asyncio aquí porque dos de nuestros pasos son asíncronos
    import asyncio
    run_full_pipeline()