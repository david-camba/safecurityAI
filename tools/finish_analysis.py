from pydantic import BaseModel, Field
from langchain_core.tools import tool

class FinishInput(BaseModel):
    summary: str = Field(description="Un breve resumen de por qué se da por finalizado el análisis.")

@tool("finish_analysis", args_schema=FinishInput)
def finish_analysis(summary: str) -> str:
    """LLAMA A ESTA HERRAMIENTA SOLO cuando el analista indique explícitamente que ha terminado todo su análisis."""
    return f"Proceso finalizado. Resumen: {summary}"