import sys
import os
import asyncio
from datetime import datetime, timedelta

# --- CONFIGURACIÓN CENTRAL DEL PIPELINE ---
# CAMBIA ESTA FECHA PARA TU PRESENTACIÓN
OPERATION_DATE_STR = "2025-09-08"

def main():
    """
    Punto de entrada único para ejecutar el pipeline completo de detección de incidencias.
    """
    print("======================================================")
    print("===   INICIANDO PIPELINE DE DETECCIÓN DE INCIDENCIAS   ===")
    print(f"===         Fecha de Operación: {OPERATION_DATE_STR}         ===")
    print("======================================================")
    
    # Importamos los módulos aquí para asegurar que el path esté configurado
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from scripts.pipeline.run_data_mining import main as run_data_mining
    from scripts.pipeline.run_incident_detection import main as run_incident_detection
    from scripts.pipeline.run_final_report import main as run_final_report

    try:
        # --- FASE 1: Minería de Datos de CVs (Se ejecuta una vez) ---
        print("\n--- [FASE 1/3] Ejecutando Data Miner Agent... ---")
        # Verificamos si el cv_data.json ya existe para no re-ejecutarlo innecesariamente
        if not os.path.exists('outputs/cv_data.json'):
            asyncio.run(run_data_mining())
            print("--- [FASE 1/3] Data Miner Agent finalizado. ---\n")
        else:
            print("--- [FASE 1/3] El archivo 'cv_data.json' ya existe. Saltando esta fase. ---\n")

        # --- FASE 2: Detección de Incidencias ---
        print("--- [FASE 2/3] Ejecutando Motor de Detección de Incidencias... ---")
        run_incident_detection(operation_date_str=OPERATION_DATE_STR)
        print("--- [FASE 2/3] Motor de Detección finalizado. ---\n")

        # --- FASE 3: Generación de Reporte Ejecutivo ---
        print("--- [FASE 3/3] Ejecutando Generador de Reporte Ejecutivo... ---")
        asyncio.run(run_final_report(operation_date_str=OPERATION_DATE_STR))
        print("--- [FASE 3/3] Generador de Reporte finalizado. ---\n")

        print("======================================================")
        print("===     PIPELINE FINALIZADO EXITOSAMENTE           ===")
        print("======================================================")

    except Exception as e:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!!   ERROR CRÍTICO DURANTE LA EJECUCIÓN DEL PIPELINE: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

if __name__ == '__main__':
    main()