import os
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class LogImprovementInput(BaseModel):
    feature: str = Field(description="La acción que se intentó realizar pero no se pudo.")
    reason: str = Field(description="Por qué es necesaria esta acción.")

@tool("log_improvement", args_schema=LogImprovementInput)
def log_improvement(feature: str, reason: str) -> str:
    """
    Registra una limitación o una capacidad faltante. 
    IMPORTANTE: Si el Analista menciona varias limitaciones distintas (ej. 'no puedo ver el registro' y 
    'no puedo aislar la red'), realiza UNA LLAMADA INDEPENDIENTE a esta herramienta para cada una de ellas.
    """
    log_file = "agent_feature_suggestions.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] FEATURE: {feature} | RAZÓN: {reason}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        return "Mejora registrada con éxito."
    except Exception as e:
        return f"Error al guardar el log: {str(e)}"