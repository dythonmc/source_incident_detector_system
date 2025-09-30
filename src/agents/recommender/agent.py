import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from .prompt import SYSTEM_PROMPT


load_dotenv()

# Este agente no necesita herramientas, solo su instrucción (prompt) para razonar.
recommender_agent = Agent(
    name="recommender_agent",
    model="gemini-2.5-pro",
    description="Analiza una incidencia y el contexto de su fuente para generar una recomendación accionable.",
    instruction=SYSTEM_PROMPT
)