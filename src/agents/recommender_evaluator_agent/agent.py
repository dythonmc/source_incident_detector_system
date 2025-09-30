import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from .prompt import SYSTEM_PROMPT

# Carga las variables del .env en la raíz del proyecto
load_dotenv()


recommender_judge_agent = Agent(
    name="recommender_judge_agent",
    model="gemini-2.5-pro",
    description="Un agente especializado en evaluar cualitativamente la respuesta del RecommenderAgent.",
    instruction=SYSTEM_PROMPT
)