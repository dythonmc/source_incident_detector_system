import sys
import os
import asyncio
from datetime import datetime

# --- CONFIGURACIÓN CENTRAL DEL PIPELINE ---
# CAMBIA ESTA FECHA PARA TU PRESENTACIÓN
OPERATION_DATE_STR = "2025-09-08"

def main():
    """
    Punto de entrada único para ejecutar el pipeline completo de detección,
    reporte y notificación de incidencias.
    """
    print("======================================================")
    print("===   INICIANDO PIPELINE DE DETECCIÓN DE INCIDENCIAS   ===")
    print(f"===         Fecha de Operación: {OPERATION_DATE_STR}         ===")
    print("======================================================")
    
    # Añadimos la ruta a 'src' para que Python encuentre nuestros módulos
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    # Importamos los módulos aquí para asegurar que el path esté configurado
    from scripts.pipeline.run_data_mining import main as run_data_mining
    from scripts.pipeline.run_incident_detection import main as run_incident_detection
    from scripts.pipeline.run_final_report import main as run_final_report
    from src.notifications.email_sender import send_report_by_email

    try:
        # --- FASE 1: Minería de Datos de CVs (Se ejecuta una vez) ---
        print("\n--- [FASE 1/4] Ejecutando Data Miner Agent... ---")
        if not os.path.exists('outputs/cv_data.json'):
            asyncio.run(run_data_mining())
            print("--- [FASE 1/4] Data Miner Agent finalizado. ---\n")
        else:
            print("--- [FASE 1/4] El archivo 'cv_data.json' ya existe. Saltando esta fase. ---\n")

        # --- FASE 2: Detección de Incidencias ---
        print("--- [FASE 2/4] Ejecutando Motor de Detección de Incidencias... ---")
        run_incident_detection(operation_date_str=OPERATION_DATE_STR)
        print("--- [FASE 2/4] Motor de Detección finalizado. ---\n")

        # --- FASE 3: Generación de Reporte Ejecutivo ---
        print("--- [FASE 3/4] Ejecutando Generador de Reporte Ejecutivo... ---")
        asyncio.run(run_final_report(operation_date_str=OPERATION_DATE_STR))
        print("--- [FASE 3/4] Generador de Reporte finalizado. ---\n")
        
        # --- FASE 4: Envío de Notificación por Email (BONUS) ---
        print("--- [FASE 4/4] Enviando Reporte Ejecutivo por Email... ---")
        report_md_path = f"outputs/{OPERATION_DATE_STR}_executive_summary.md"
        
        # Asumiendo que el envío de email funciona (como indicaste), lo ejecutamos.
        # Si falla, el pipeline continuará y mostrará un error, pero no se detendrá.
        send_report_by_email(report_path=report_md_path, operation_date=OPERATION_DATE_STR)
        print("--- [FASE 4/4] Proceso de notificación finalizado. ---\n")


        print("======================================================")
        print("===     PIPELINE FINALIZADO EXITOSAMENTE           ===")
        print("======================================================")

    except Exception as e:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!!   ERROR CRÍTICO DURANTE LA EJECUCIÓN DEL PIPELINE: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

if __name__ == '__main__':
    main()