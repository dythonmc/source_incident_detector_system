import os
from dotenv import load_dotenv # <--- NUEVA IMPORTACIÓN
from google.adk.agents import Agent
from .prompt import SYSTEM_PROMPT

# <--- NUEVA LÍNEA: Carga las variables del .env en la raíz del proyecto
load_dotenv()

# Este agente no necesita herramientas, solo su instrucción (prompt) para razonar.
recommender_agent = Agent(
    name="recommender_agent",
    model="gemini-2.5-pro",
    description="Analiza una incidencia y el contexto de su fuente para generar una recomendación accionable.",
    instruction=SYSTEM_PROMPT
)