# **Sistema de Detección de Incidencias con Agentes de IA**
<br>

## **1. Resumen del Proyecto**
Este proyecto implementa un pipeline automatizado de extremo a extremo para el monitoreo, detección y análisis de incidencias en el procesamiento de archivos. El sistema está construido como una arquitectura multi-agente donde diferentes agentes especializados, construidos con el framework `google-adk`, colaboran para cumplir el objetivo.

El diseño se basa en un enfoque híbrido: se utiliza lógica determinística para tareas que requieren una precisión del 100% (el motor de detección), mientras que se delegan a los **agentes de IA** las tareas que involucran razonamiento, comprensión de lenguaje no estructurado y generación de contenido cualitativo.

<br>

**Diagrama Diseño**
![Diagrama de Arquitectura del Sistema de Detección de Incidencias](docs/architecture.svg)


## **2. Arquitectura Multi-Agente**
El sistema no es una aplicación monolítica, sino un ecosistema de agentes que se orquestan para realizar tareas complejas. Cada agente tiene una única responsabilidad, lo que hace que el sistema sea modular, escalable y fácil de mantener.

**El flujo del pipeline está orquestado por la colaboración de los siguientes agentes:**

### 2.1. Agentes de Operacion.
`DataMinerAgent`:

- **Rol:** El Extractor de Conocimiento.

- **Tarea:** Su misión es leer los documentos CV de cada fuente, que están en formato Markdown semi-estructurado, y extraer los patrones clave (horarios, volúmenes esperados, etc.).

- **Capacidades (Tools):** Está equipado con una FunctionTool que le permite leer el contenido de los archivos del sistema.

- **Resultado:** Produce el cv_data.json, que sirve como la "memoria" o base de conocimiento para el resto del sistema.

`RecommenderAgent`:

- **Rol:** El Analista de Operaciones.

- **Tarea:** Recibe una incidencia técnica (datos estructurados) y el contexto de la fuente (del cv_data.json). Su objetivo es razonar sobre el problema y generar una recomendación clara y útil en lenguaje natural para el equipo de operaciones.

- **Capacidades (Tools):** No utiliza herramientas externas. Su valor reside puramente en su capacidad de razonamiento y generación de lenguaje (LLM).

- **Resultado:** Enriquece el reporte de incidencias con una capa de inteligencia accionable.

### 2.2. Agentes de Evaluación.
Una parte fundamental del diseño es la capacidad del sistema para auto-evaluarse. Para ello, hemos construido un framework de evaluación que también se basa en agentes.

`DataMinerEvaluator`:

- **Rol:** El Auditor de Precisión.

- **Tarea:** Este pipeline de evaluación ejecuta el `DataMinerAgent` sobre un caso de prueba y compara su salida JSON campo por campo contra un "ground truth" (un JSON perfecto creado manualmente).

- **Resultado:** Genera un reporte con métricas de **Precisión y Completitud**, y crea un log (evaluation_log.json) para rastrear el rendimiento del agente a lo largo del tiempo.

`RecommenderEvaluatorAgent`:

- **Rol:** El Juez de Calidad.

- **Tarea:** Implementa el patrón avanzado `"LLM-as-a-Judge"`. Este agente recibe una incidencia, una recomendación "ideal" (ground truth) y la recomendación generada por el `RecommenderAgent`.

- **Capacidades (Tools):** No usa herramientas; su función es el razonamiento cualitativo.

- **Resultado:** Emite un veredicto en formato JSON que incluye **una puntuación de calidad (de 1 a 5)** y una justificación de por qué la recomendación del `RecommenderAgent` fue buena o mala. Este resultado también se registra en un log.

`FeedbackEvaluatorAgent`:

- **Rol:** El Analista de Feedback.

- **Tarea:** Compara el reporte de incidencias completo de nuestro sistema con el feedback semi-estructurado proporcionado por los stakeholders humanos.

- **Capacidades (Tools):** Está equipado con una `FunctionTool` (`parse_feedback_excel_file`) que le permite leer y estructurar el archivo de feedback.

- **Resultado:** Genera un **plan de acción de mejora** en formato JSON, identificando posibles falsos positivos o falsos negativos y sugiriendo dónde se debe refinar la lógica de los detectores.

<br>

## **3. Paso a Paso del Flujo del Sistema**
***FASE DE PIPELINE (Ejecución de Producción)***

**Paso 1: Preparación y Extracción de Conocimiento**

- **1.1: Recolección de Datos Crudos:** Se toman los ``files.json``, la carpeta ``datasource_cvs/`` y el archivo ``Feedback.xlsx.``

- **1.2: Carga con data_loader:** El módulo ``src/preparation/data_loader.py`` carga los datos de operación (``files.json``) en un DataFrame.

- **1.3: ``DataMinerAgent`` extrae la Inteligencia:** El ``DataMinerAgent`` lee los archivos ``.md`` no estructurados y los transforma en el archivo ``outputs/cv_data.json``, que es la base de conocimiento del sistema.

**Paso 2: Detección Determinística de Incidencias**

- **2.1: El Motor Lógico se Activa:** El script ``run_incident_detection.py`` itera sobre cada fuente conocida.

- **2.2: Cruce de Datos vs. Inteligencia:** El módulo ``src/detection/detectors.py`` aplica 6 reglas de negocio precisas, comparando los datos del día con los patrones del ``cv_data.json.``

- **2.3: Salida Técnica:** Se genera el reporte ``outputs/{fecha}_incidents_report.json`` con una lista estructurada de todos los problemas encontrados.

**Paso 3: Enriquecimiento y Reporte Ejecutivo con IA**

- **3.1: Clasificación de Severidad:** El módulo ``src/reporting/consolidator.py`` lee el reporte de incidencias y asigna un nivel de criticidad (🔴 URGENTE, 🟡 REQUIERE ATENCIÓN, TODO BIEN 🟢) a cada fuente.

- **3.2: ``RecommenderAgent`` Genera Insights:** El ``RecommenderAgent`` analiza cada incidencia y, basándose en el contexto del CV, genera una recomendación accionable en lenguaje natural.

- **3.3: Salida Ejecutiva:** Se generan los reportes finales en ``outputs/``: un ``.md`` para humanos y un .``json`` para otros sistemas.

**Paso 4: Notificación (Bonus)**

- **4.1: Envío de Alerta:** El módulo ``src/notifications/email_sender.py`` toma el reporte .md, lo convierte a HTML y lo envía por email a los stakeholders.

<br>

## **4. Estructura del Proyecto**
El proyecto sigue una estructura profesional que separa claramente los intereses (Separation of Concerns):

```
/
├── src/              # Código fuente de la aplicación (módulos reutilizables).
|   |── agents/       # Agentes de operacion y evaluación.
├── scripts/          # Scripts ejecutables (puntos de entrada).
│   ├── pipeline/     # Scripts que forman el pipeline de producción.
│   └── evaluation/   # Scripts para evaluar la calidad de los agentes.
├── data/             # Datos de entrada crudos.
├── outputs/          # Archivos generados por el pipeline (reportes, JSONs).
├── evaluation/       # "Ground truth" y logs de las evaluaciones.
├── .env              # Archivo para variables de entorno (API |Keys, credenciales).
└── requirements.txt  # Dependencias del proyecto.
```

<br>

## **5. Guía de Instalación**
Sigue estos pasos para configurar el entorno de desarrollo.

1. **Clonar el Repositorio:**
```
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
```
2. **Crear y Activar el Ambiente Virtual:**

```
python -m venv venv
# En Windows
.\venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```
3. **Instalar Dependencias:**
Asegúrate de tener todas las librerías necesarias instaladas ejecutando:

```
pip install -r requirements.txt
```
4. **Configurar Variables de Entorno:**
Crea un archivo .env en la raíz del proyecto, añadiendo tus propias claves:

```
# Clave para los agentes de IA de Google
GOOGLE_API_KEY="tu_api_key_de_google"

# Credenciales para el envío de email (se recomienda usar una Contraseña de Aplicación)
EMAIL_SENDER="tu_correo@ejemplo.com"
EMAIL_PASSWORD="tu_contraseña_de_aplicacion"
EMAIL_RECIPIENT="correo_destino@ejemplo.com"
```

<br>

## 6. **Guía de Uso del Sistema**
Ejecutar el Pipeline Completo
Para ejecutar todo el proceso de forma automática para un día específico, configura la fecha en el script principal y ejecútalo desde la raíz del proyecto.

1. Abre el archivo `run_pipeline.py`.

2. Modifica la variable `OPERATION_DATE_STR` a la fecha deseada.

3. Ejecuta el script:

```
python run_pipeline.py
```

Esto ejecutará la minería de datos (si es necesario), la detección, la generación de reportes y el envío de la notificación por email.

**Ejecutar Módulos Individualmente**

Para desarrollo y depuración, puedes ejecutar cada fase del pipeline y las evaluaciones de forma independiente usando el modo módulo de Python (`-m`). **Asegúrate de ejecutar estos comandos desde la raíz del proyecto.**

- **Fase 1: Minería de Datos:**

```
python -m scripts.pipeline.run_data_mining
```

- **Fase 2: Detección de Incidencias:**
```
python -m scripts.pipeline.run_incident_detection
```
- **Fase 3: Reporte Ejecutivo:**

```
python -m scripts.pipeline.run_final_report
```

- **Bonus: Enviar Notificación:**

```
python -m scripts.pipeline.run_send_report
```
#### **Ejecutar las Evaluaciones de Agentes**
- **Evaluar el `DataMinerAgent` (Precisión de Extracción):**

```
python -m scripts.evaluation.run_dataminer_evaluation
```
- **Evaluar el `RecommenderAgent` (Calidad de Recomendación):**

```
python -m scripts.evaluation.run_recommender_evaluation
```
- **Evaluar el Sistema vs. Feedback Humano:**
```
python -m scripts.evaluation.run_feedback_evaluation
```

## **7. Componentes Clave y Diseño**
- **Diseño Híbrido:** El sistema combina lógica determinística para tareas que requieren 100% de precisión (detección de incidencias) con Agentes de IA para tareas que involucran lenguaje no estructurado y razonamiento (minería de CVs, recomendaciones).

- **Framework de Agentes ``google-adk``:** Se utiliza para definir agentes especializados y modulares, cada uno con un propósito claro y, en su caso, herramientas específicas.

- **Framework de Evaluación Continua:** El proyecto incluye un robusto sistema de evaluación que permite medir la calidad de cada componente de IA de forma cuantitativa y cualitativa, sentando las bases para la mejora continua y MLOps.


<br>

[**Ver Demostración Completa en Loom**](https://www.loom.com/share/beedb0e2fe8f458a8b32be5969b49bcd?sid=f765f29f-7645-43a8-a29c-5885a63fe17c)

https://www.loom.com/share/beedb0e2fe8f458a8b32be5969b49bcd?sid=f765f29f-7645-43a8-a29c-5885a63fe17c


## **8. Demostracion Ejecuccion y Outputs.**
**1. Operacion:**

Basandose en la data cruda y seleccionando un dia de operacion se ejecuta el pipeline:


python run_pipeline.py

```
======================================================
===   INICIANDO PIPELINE DE DETECCIÓN DE INCIDENCIAS   ===
===         Fecha de Operación: 2025-09-08         ===
======================================================
```

Se cargan lo datos iniciales y se activa el agente Data Miner para extraer la informacion de los CVs.


```
--- [FASE 1/4] Ejecutando Data Miner Agent... ---
--- Iniciando el Proceso de Minería de Datos de CVs (Patrón ADK Async Runner) ---
Se encontraron 18 archivos CV para procesar en total.

--- Procesando CV para source_id: 195385 ---
Warning: there are non-text parts in the response: ['thought_signature', 'function_call'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Warning: there are non-text parts in the response: ['thought_signature', 'function_call'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Warning: there are non-text parts in the response: ['thought_signature'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
✓ Extracción exitosa para source_id: 195385
```
El agente itera un total de fuentes(n) y ese es el numero de peticiones al api

```
--- Proceso completado. 18 CVs procesados exitosamente. ---
✓ Los datos estructurados han sido guardados en: outputs/cv_data.json
--- [FASE 1/4] Data Miner Agent finalizado. ---
```

*importante*: si el sistema encuentra que ya se hizo la mineria previamente entonces salta esta parte y el agente no trabaja.

Una vez termina de iterar y minar los datos de los CVs crea un reporte en outputs/cv_data.json de esta naturaleza:

```
cv.data.json
[
  {
    "resource_id": "195385",
    "general_volume_stats": {
      "mean_rows": null,
      "median_rows": null,
      "stdev_rows": null,
      "pct_empty_files": 0.0
    },
    "file_processing_daily_stats": [
      {"day": "Mon","mean_files": 0,"median_files": 0},
      {"day": "Tue","mean_files": 40,"median_files": 38},
      {"day": "Wed","mean_files": 32,"median_files": 37},
      {"day": "Thu","mean_files": 37,"median_files": 37},
      {"day": "Fri","mean_files": 45,"median_files": 38},
      {"day": "Sat","mean_files": 36,"median_files": 36},
      {"day": "Sun","mean_files": 0,"median_files": 0}
    ],
    "upload_schedule_daily_stats": [
      {"day": "Mon","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      {"day": "Tue","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      {"day": "Wed","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      { "day": "Thu","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      { "day": "Fri","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      { "day": "Sat","upload_window_expected_utc": "08:00:00–09:00:00 UTC"},
      { "day": "Sun","upload_window_expected_utc": null}
    ],
    "day_of_week_row_stats": [
      {"day": "Mon","rows_mean": 13.25,"rows_median": 2.0,"empty_files_mean": 0.0},
      {"day": "Tue","rows_mean": 1077272.33,"rows_median": 984344.0,"empty_files_mean": 0.0},
      {"day": "Wed","rows_mean": 1406818.17,"rows_median": 1465666.0,"empty_files_mean": 0.0},
      {"day": "Thu","rows_mean": 565671.92,"rows_median": 518463.5,"empty_files_mean": 0.0},
      {"day": "Fri","rows_mean": 571679.0,"rows_median": 540203.5,"empty_files_mean": 0.0},
      {"day": "Sat","rows_mean": 566643.33,"rows_median": 573718.0,"empty_files_mean": 0.0},
      {"day": "Sun","rows_mean": 0.0,"rows_median": 0.0,"empty_files_mean": 0.0}
    ],
    "insights_for_incidences": [
      "Beneficios entity shows an unusual Friday spike pattern (14.60 files vs. typical 1-2 files).",
      "Files appearing on Sunday would be anomalous (consistently zero in historical data).",
      "Files with formats other than CSV would be anomalous (100% CSV historically).",
      "Monday shows minimal activity (mean 1 file overall) with a wider time window (08:06-17:21 UTC).",
      "Most uploads are expected Tuesday-Saturday within 08:00-08:13 UTC.",
      "Saipos entity shows Monday activity (5.50 files) which differs from most entities.",
      "Significant deviations from entity-specific volume patterns would be anomalous.",
      "Wednesday consistently shows the highest volume."
    ],
    "source_id": "195385"
  },
  
```
Con esta información disponible se ejecuta el motor de incidencias.

```
--- [FASE 2/4] Ejecutando Motor de Detección de Incidencias... ---
--- [DETECCIÓN] Iniciando para el día: 2025-09-08 ---
[1/3] Cargando datos...
--- Iniciando carga de 'files.json' para la fecha: 2025-09-08 ---
✓ Se transformaron 3600 registros totales desde el JSON.
✓ Se filtraron 19 archivos que corresponden a la fecha 2025-09-08.
--- Proceso de carga y filtrado finalizado. ---
[2/3] Ejecutando detectores para cada fuente...
--- Analizando Fuente: 195385 ---
--- Analizando Fuente: 195436 ---
--- Analizando Fuente: 195439 ---
--- Analizando Fuente: 196125 ---
--- Analizando Fuente: 199944 ---
--- Analizando Fuente: 207936 ---
--- Analizando Fuente: 207938 ---
--- Analizando Fuente: 209773 ---
--- Analizando Fuente: 211544 ---
--- Analizando Fuente: 220504 ---
--- Analizando Fuente: 220505 ---
--- Analizando Fuente: 220506 ---
--- Analizando Fuente: 224602 ---
--- Analizando Fuente: 224603 ---
--- Analizando Fuente: 228036 ---
--- Analizando Fuente: 228038 ---
--- Analizando Fuente: 239611 ---
--- Analizando Fuente: 239613 ---
[3/3] Consolidando y guardando reporte de incidencias...
✓ Reporte de 10 incidencias guardado en: outputs\2025-09-08_incidents_report.json
--- [FASE 2/4] Motor de Detección finalizado. ---
```
Una vez es ejecutado el motor de deteccion se guarda la informacion del resultado en outputs en un archivo json.

el output se ve asi:
```
2025-09-08_incidents_report.json
[
  {
    "source_id": "196125",
    "incident_type": "Archivos Faltantes",
    "incident_details": "Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histórica para los Mon es 2.00).",
    "total_incidentes": 2,
    "files_to_review": []
  },
  {
    "source_id": "207938",
    "incident_type": "Variación de Volumen Inesperada",
    "incident_details": "Se encontraron 3 archivos con un número de filas anómalo. La media esperada para los Mon es ~436869 (stdev: 16949).",
    "total_incidentes": 3,
    "files_to_review": [
      "3_Soop_CONC_20250907_M___POS_MARKETPLACE_5B25A3F571D6400082B1E5E228A3E401_14380200000121_0000.csv",
      "3_Soop_CONC_20250907_M___PAGO_688B810A3E464D27B9E8AAE31C02CE91_02599377000134_0000.csv",
      "3_Soop_CONC_20250907_M__SHOP_MARKETPLACE_046F9EC9F801495790B8182D16D66C6A_14380200000121_0000.csv"
    ]
  },
```

Una vez tenemos el reporte de incidentes contratamos al agente Recommender para revisar los CVs vs el reporte de incidentes y dejar una sugerencia.
```
--- [FASE 3/4] Ejecutando Generador de Reporte Ejecutivo... ---
--- [REPORTE] Iniciando para el día: 2025-09-08 ---

[1/4] Cargando datos de incidencias y CVs...

[2/4] Clasificando la severidad para cada fuente...

[3/4] Generando recomendaciones con el Agente de IA...
   -> Obteniendo recomendaciones para la fuente: 196125...
   -> Obteniendo recomendaciones para la fuente: 207938...
   -> Obteniendo recomendaciones para la fuente: 220504...
   -> Obteniendo recomendaciones para la fuente: 220505...
   -> Obteniendo recomendaciones para la fuente: 220506...
   -> Obteniendo recomendaciones para la fuente: 228036...
   -> Obteniendo recomendaciones para la fuente: 228038...
   -> Obteniendo recomendaciones para la fuente: 239611...
   -> Obteniendo recomendaciones para la fuente: 239613...

[4/4] Creando los archivos de reporte finales...
✓ Reporte JSON enriquecido guardado en: outputs\2025-09-08_executive_summary.json
   -> Generando reporte en formato Markdown...
✓ Reporte Markdown guardado en: outputs\2025-09-08_executive_summary.md
--- [FASE 3/4] Generador de Reporte finalizado. ---

```
Una vez termina de iterar sobre todas las fuentes para obtener la recomendación genera dos reportes:

ejemplo del output para 1 fuente.

```
executive_summary.json

      {
        "source_id": "220504",
        "incident_type": "Archivos Faltantes",
        "incident_details": "Se recibieron 4 archivos, pero se esperaban aproximadamente 16 (la media histÃ³rica para los Mon es 16.00).",
        "total_incidentes": 12,
        "files_to_review": [
          "QkRq2GdOiYcED6w__BR_Saipos_payments_accounting_report_2025_09_07.csv",
          "QkRq0GTSCYcEkvA__BR_Anotaai_Wallet_payments_accounting_report_2025_09_07.csv",
          "QkRqxGJmiYcEnrQ__BR_safemode_payments_accounting_report_2025_09_07.csv",
          "QkRqvEzQCYcEmgQ__BR_DataOnly_payments_accounting_report_2025_09_07.csv"
        ],
        "recommendation": "Contactar al proveedor para investigar la ausencia de los 12 archivos esperados para el lunes, un día con patrón de entrega altamente consistente y hora de subida alrededor de las 08:00 UTC."
      }

```
y un archivo markdown asi:
````
# Reporte Diario de Incidencias de Procesamiento
**Fecha de Análisis:** 2025-09-08

## Resumen del Día
Se analizaron las fuentes de datos y se encontraron **0** fuentes con criticidad **URGENTE** y **9** que **REQUIEREN ATENCIÓN**.

---
## 🟡 REQUIERE ATENCIÓN - Necesita Investigación

### Fuente: `196125` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar la ausencia de archivos con el proveedor, considerando que los lunes son días de bajo volumen donde la mediana histórica de archivos recibidos es 0.
````
Una vez tenemos esta informacion, se envia el reporte por correo de forma automatica.

```
--- [FASE 4/4] Enviando Reporte Ejecutivo por Email... ---
-> Conectando al servidor SMTP para enviar el reporte a danielmogollonc55@gmail.com...
✓ ¡Reporte enviado por email exitosamente!
--- [FASE 4/4] Proceso de notificación finalizado. ---

======================================================
===     PIPELINE FINALIZADO EXITOSAMENTE           ===
======================================================
```

<br>
<br>

2. Evaluacion.

Una vez corremos el pipeline de operacion y con los outputs listos, entonces podemos pasar a la evaluacion tanto de los agentes operadores como del reporte final del sistema.

Buscando la escalabilidad y la modularidad cada test se ejecuta por separado.

Tenemos 3 evaluaciones.

DataMiner Evaluation se ejecuta: run_dateminer_evaluation.py
```
--- Iniciando Evaluación para el Agente: DataMinerAgent ---
--- Archivo de Prueba: 207936_native.md ---

[1/4] Ejecutando el DataMinerAgent para obtener la predicción...
Warning: there are non-text parts in the response: ['thought_signature', 'function_call'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Warning: there are non-text parts in the response: ['thought_signature'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
✓ Predicción del agente obtenida y parseada correctamente.

[2/4] Cargando el archivo de Ground Truth...
✓ Ground Truth cargado desde 'evaluation/data_miner/ground_truth_cv_207936.json'.

[3/4] Comparando predicción con Ground Truth y generando reporte...

--- REPORTE DE EVALUACIÓN: DataMinerAgent ---
============================================
  Precisión de Campos (Accuracy): 77.78%
  Completitud de Campos (Completeness): 100.00%
--------------------------------------------

Campos con Valores Incorrectos:
  - Campo: upload_schedule_daily_stats
    - Esperado: [{'day': 'Mon', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Tue', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Wed', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Thu', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Fri', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Sat', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}, {'day': 'Sun', 'upload_window_expected_utc': '11:00:00â€“11:00:00 UTC'}]
    - Recibido:   [{'day': 'Mon', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Tue', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Wed', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Thu', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Fri', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Sat', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}, {'day': 'Sun', 'upload_window_expected_utc': '11:00:00–11:00:00 UTC'}]
  - Campo: insights_for_incidences
    - Esperado: ['Empty files (31.9%) are predominantly associated with __POS channel.', 'Upload timing is extremely consistent in an 11:01-11:44 UTC window.', 'Weekend files are typically uploaded on Monday.', 'Absence of weekday uploads would be anomalous.']
    - Recibido:   ['Absence of weekday uploads would be anomalous.', 'Empty file pattern: 31.9% of files contain 0 rows; predominantly __POS channel files.', 'Consistent 3 files per day pattern (mode=3) across all days of week.', 'Friday shows exceptional peak volume.', 'Extremely consistent timing (11:01-11:44 UTC).', 'Weekend files typically uploaded Monday (lag = 1-2 days).']

============================================

[4/4] Guardando resultados en el log de evaluación JSON...
✓ Resultados guardados exitosamente en 'evaluation/data_miner/evaluation_log.json' 
```


Este agente hace la evaluacion y escribe el resultado en un archivo .json

```
[
    {
        "timestamp_utc": "2025-09-29T20:20:21.167914+00:00",
        "agent_evaluated": "DataMinerAgent",
        "test_case": "207936_native.md",
        "accuracy_score": "77.78%",
        "completeness_score": "100.00%",
        "mismatched_count": 2,
        "missing_count": 0,
        "prompt_version": "v1.0"
    }
]
```

Este es el resultado que nos ayuda a iterar para mejorar en la extraccion.

Luego esta el RecommenderEvaluatorAgent quien nos ayuda a evaluar el reporte final con la recomendacion del agente.

```
--- Iniciando Evaluación Cualitativa con RecommenderJudgeAgent ---

[1/5] Cargando caso de prueba y contexto...
✓ Caso de prueba y contexto cargados.

[2/5] Ejecutando el RecommenderAgent...
✓ Recomendación del agente obtenida.

[3/5] Ejecutando el RecommenderJudgeAgent...
✓ Veredicto del Juez recibido.

[4/5] Mostrando resultados de la evaluación...
   !! El juez no devolvió un JSON válido.

--- REPORTE DE EVALUACIÓN CUALITATIVA: RecommenderAgent ---
==========================================================
   - Puntuación (Score): 0.0 / 5.0
   - Justificación: Respuesta no válida del Juez: ```json
{
  "score": 2.7,
  "justification": "La recomendación del agente contiene un error fáctico grave al afirmar que se esperaban '~16' archivos, cuando la incidencia especifica claramente que la media es ~4. Este dato incorrecto exagera la severidad del problema, calificándolo de 'desviación crítica'. Aunque la acción sugerida ('Contactar al proveedor') es correcta y coincide con la ideal, la justificación errónea compromete severamente su relevancia y fiabilidad."
}

==========================================================

[5/5] Guardando resultados en el log de evaluación...
✓ Resultados guardados exitosamente en 'evaluation/recommender/evaluation_results/evaluation_log.json'
```

Este agente evalua el resultado y deja el reporte de la evaluacion en un json:

```
[
    {
        "timestamp_utc": "2025-09-29T21:15:38.228503+00:00",
        "agent_evaluated": "RecommenderAgent",
        "test_case_id": "rec_eval_01_missing_files",
        "prompt_version": "v1.0",
        "score": 0.0,
        "justification": "Respuesta no válida del Juez: ```json\n{\n  \"score\": 2.7,\n  \"justification\": \"La recomendación del agente contiene un error fáctico grave al afirmar que se esperaban '~16' archivos, cuando la incidencia especifica claramente que la media es ~4. Este dato incorrecto exagera la severidad del problema, calificándolo de 'desviación crítica'. Aunque la acción sugerida ('Contactar al proveedor') es correcta y coincide con la ideal, la justificación errónea compromete severamente su relevancia y fiabilidad.\"\n}\n```",
        "golden_recommendation": "Contactar al proveedor de la fuente 220504 para investigar por quÃ© falta 1 archivo esperado para el lunes, que es un dÃ­a de alto volumen. Verificar si hay retrasos conocidos en la entrega.",
        "agent_recommendation": "Contactar urgentemente al proveedor. Se recibieron solo 3 archivos en lugar de los ~16 esperados para un lunes, lo que representa una desviación crítica."
    }
]
``` 
<br>
 
<br>
Finalmente tenemos nuestro FeedbackEvaluatorAgent que nos ayuda a classificar finalmente el sistema:

```
--- Iniciando Evaluación con Agente (con Tool) vs. Feedback Humano ---

[1/4] Cargando incidencias generadas por el sistema...
✓ Se cargaron 10 tipos de incidencias del sistema.

[2/4] Ejecutando el FeedbackEvaluatorAgent...
Warning: there are non-text parts in the response: ['thought_signature', 'function_call'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
Warning: there are non-text parts in the response: ['thought_signature'], returning concatenated text result from text parts. Check the full candidates.content.parts accessor to get the full model response.
✓ El Agente de Evaluación de Feedback ha finalizado su análisis.

[3/4] Plan de Acción de Mejora generado por el Agente:
=====================================================
1. VALIDACIÓN EXITOSA: La detección para la fuente 207938 está alineada con el feedback. Considerar si la 'acción humana' del feedback puede usarse para mejorar las recomendaciones automáticas.
2. VALIDACIÓN EXITOSA: La detección para la fuente 228036 está alineada con el feedback. Considerar si la 'acción humana' del feedback puede usarse para mejorar las recomendaciones automáticas.
3. VALIDACIÓN EXITOSA: La detección para la fuente 228038 está alineada con el feedback. Considerar si la 'acción humana' del feedback puede usarse para mejorar las recomendaciones automáticas.
4. VALIDACIÓN EXITOSA: La detección para la fuente 239611 está alineada con el feedback. Considerar si la 'acción humana' del feedback puede usarse para mejorar las recomendaciones automáticas.
5. VALIDACIÓN EXITOSA: La detección para la fuente 239613 está alineada con el feedback. Considerar si la 'acción humana' del feedback puede usarse para mejorar las recomendaciones automáticas.
6. INVESTIGAR FALSOS NEGATIVOS: Revisar la lógica del detector para la fuente 195385 ya que omitió incidencias reportadas por humanos.
7. INVESTIGAR FALSOS NEGATIVOS: Revisar la lógica del detector para la fuente 211544 ya que omitió incidencias reportadas por humanos.
8. INVESTIGAR FALSOS NEGATIVOS: Revisar la lógica del detector para la fuente 209773 ya que omitió incidencias reportadas por humanos.
9. ANALIZAR FALSOS POSITIVOS: Validar por qué el sistema reportó incidencias en la fuente 196125 que no fueron consideradas relevantes por el equipo.
10. ANALIZAR FALSOS POSITIVOS: Validar por qué el sistema reportó incidencias en la fuente 220504 que no fueron consideradas relevantes por el equipo.
11. ANALIZAR FALSOS POSITIVOS: Validar por qué el sistema reportó incidencias en la fuente 220505 que no fueron consideradas relevantes por el equipo.
12. ANALIZAR FALSOS POSITIVOS: Validar por qué el sistema reportó incidencias en la fuente 220506 que no fueron consideradas relevantes por el equipo.
=====================================================

[4/4] Guardando el log de la evaluación en un archivo JSON...
✓ Log de evaluación guardado exitosamente en 'evaluation/feedback_evaluator/evaluation_results/evaluation_log.json'
```

Este agente guarda la informacion del resultado en las evaluaciones con un archivo tipo json:

```
[
    {
        "timestamp_utc": "2025-09-29T22:32:52.684022+00:00",
        "agent_evaluated": "FeedbackEvaluatorAgent",
        "operation_date": "2025-09-08",
        "agent_action_plan": [
            "VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 207938 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n humana' del feedback puede usarse para mejorar las recomendaciones autom\u00e1ticas.",
            "VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 228036 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n humana' del feedback puede usarse para mejorar las recomendaciones autom\u00e1ticas.",
            "VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 228038 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n humana' del feedback puede usarse para mejorar las recomendaciones autom\u00e1ticas.",
            "VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 239611 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n humana' del feedback puede usarse para mejorar las recomendaciones autom\u00e1ticas.",
            "VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 239613 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n humana' del feedback puede usarse para mejorar las recomendaciones autom\u00e1ticas.",
            "INVESTIGAR FALSOS NEGATIVOS: Revisar la l\u00f3gica del detector para la fuente 195385 ya que omiti\u00f3 incidencias reportadas por humanos.",
            "INVESTIGAR FALSOS NEGATIVOS: Revisar la l\u00f3gica del detector para la fuente 211544 ya que omiti\u00f3 incidencias reportadas por humanos.",
            "INVESTIGAR FALSOS NEGATIVOS: Revisar la l\u00f3gica del detector para la fuente 209773 ya que omiti\u00f3 incidencias reportadas por humanos.",
            "INVESTIGAR FALSOS NEGATIVOS: Revisar la l\u00f3gica del detector para la fuente 224603 ya que omiti\u00f3 incidencias reportadas por humanos.",
            "ANALIZAR FALSOS POSITIVOS: Validar por qu\u00e9 el sistema report\u00f3 incidencias en la fuente 196125 que no fueron consideradas relevantes por el equipo.",
            "ANALIZAR FALSOS POSITIVOS: Validar por qu\u00e9 el sistema report\u00f3 incidencias en la fuente 220504 que no fueron consideradas relevantes por el equipo.",
            "ANALIZAR FALSOS POSITIVOS: Validar por qu\u00e9 el sistema report\u00f3 incidencias en la fuente 220505 que no fueron consideradas relevantes por el equipo.",
            "ANALIZAR FALSOS POSITIVOS: Validar por qu\u00e9 el sistema report\u00f3 incidencias en la fuente 220506 que no fueron consideradas relevantes por el equipo."
        ],
        "raw_agent_response": "```json\n{\n  \"action_plan\": [\n    \"VALIDACI\u00d3N EXITOSA: La detecci\u00f3n para la fuente 207938 est\u00e1 alineada con el feedback. Considerar si la 'acci\u00f3n`" ...... se acorta mensaje para visualizacion
    }
]
```


Con esto finalmente tenemos todo el sistema ejecutado:
1. Operacion
2. Evaluacion