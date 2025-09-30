import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from .prompt import SYSTEM_PROMPT
from .tools import parse_feedback_tool

load_dotenv()

feedback_evaluator_agent = Agent(
    name="feedback_evaluator_agent",
    model="gemini-2.5-pro",
    description="Un agente que evalúa la calidad de la detección de incidencias comparándola con el feedback humano.",
    instruction=SYSTEM_PROMPT,
    tools=[parse_feedback_tool]
)