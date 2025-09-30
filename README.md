# **Sistema de Detección de Incidencias con Agentes de IA**
<br>

## **1. Resumen del Proyecto**
Este proyecto implementa un pipeline automatizado de extremo a extremo para el monitoreo, detección y análisis de incidencias en el procesamiento de archivos. El sistema está construido como una arquitectura multi-agente donde diferentes agentes especializados, construidos con el framework `google-adk`, colaboran para cumplir el objetivo.

El diseño se basa en un enfoque híbrido: se utiliza lógica determinística para tareas que requieren una precisión del 100% (el motor de detección), mientras que se delegan a los **agentes de IA** las tareas que involucran razonamiento, comprensión de lenguaje no estructurado y generación de contenido cualitativo.

<br>

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

## **3. Estructura del Proyecto**
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

## **4. Guía de Instalación**
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

## 5. **Guía de Uso del Sistema**
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

## 6. Componentes Clave y Diseño
- **Diseño Híbrido:** El sistema combina lógica determinística para tareas que requieren 100% de precisión (detección de incidencias) con Agentes de IA para tareas que involucran lenguaje no estructurado y razonamiento (minería de CVs, recomendaciones).

- **Framework de Agentes ``google-adk``:** Se utiliza para definir agentes especializados y modulares, cada uno con un propósito claro y, en su caso, herramientas específicas.

- **Framework de Evaluación Continua:** El proyecto incluye un robusto sistema de evaluación que permite medir la calidad de cada componente de IA de forma cuantitativa y cualitativa, sentando las bases para la mejora continua y MLOps.