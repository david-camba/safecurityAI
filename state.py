from typing import TypedDict, List, Annotated
import operator

# ==========================================
# 1. DEFINICIÓN DEL ESTADO (La Memoria Compartida)
# ==========================================

class AgentState(TypedDict):
    """
    Este es el estado que viajará por todo el grafo.
    Annotated con operator.add significa que las listas se concatenarán, 
    no se sobrescribirán (perfecto para un historial).
    """
    system_data: str  # El volcado MASIVO del script de PowerShell (solo lectura)
    history: Annotated[List[dict], operator.add]  # Historial de iteraciones: Analyst <-> Tools
    iteration_count: int  # Para evitar bucles infinitos (límite de 10)
    
    # Flags de control gestionadas por el Supporter
    is_finished: bool  # Si es True, nos vamos al Formatter
    tool_requests: list  # NUEVO: Lista de herramientas a ejecutar (si las hay)
    
    # Resultado final
    final_report: str