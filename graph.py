from state import AgentState
from langgraph.graph import StateGraph, END
from nodes import analyst_node, supporter_node, tool_execution_node, formatter_node

def route_from_supporter(state: AgentState):
    """
    Decide a qué nodo ir después del Supporter.
    """
    # 1. Protección contra bucles infinitos
    if state["iteration_count"] >= 10:
        print("[AVISO] Límite de iteraciones. Forzando fin.")
        return "to_formatter"
        
    # 2. Si el Supporter detecta que el Analista ya ha terminado
    if state.get("is_finished", False):
        return "to_formatter"
        
    # 3. NUEVO: Si no ha terminado, PERO no ha pedido usar herramientas
    # (Solo quiere analizar otra parte del documento)
    #if not state.get("tool_requests"):
    #print("[ROUTER] No hay herramientas solicitadas. Volviendo al Analista...")
    return "to_analyst"
        
    # 4. Si no ha terminado y SÍ hay herramientas en la lista
    print(f"[ROUTER] Herramientas solicitadas: {len(state['tool_requests'])}. Ejecutando...")
    return "to_tools"

# ==========================================
# 4. CONSTRUCCIÓN DEL GRAFO LANGGRAPH
# ==========================================

workflow = StateGraph(AgentState)

# Añadimos los nodos
workflow.add_node("analyst", analyst_node)
workflow.add_node("supporter", supporter_node)
#workflow.add_node("tools", tool_execution_node)
workflow.add_node("formatter", formatter_node)

# Definimos las conexiones (Aristas)
workflow.set_entry_point("analyst") # Todo empieza en el Analista

workflow.add_edge("analyst", "supporter") # El analista siempre le pasa la pelota al Supporter

# Del Supporter salen varios caminos (Lógica Condicional)
workflow.add_conditional_edges(
    "supporter",
    route_from_supporter,
    {
        #"to_tools": "tools",
        "to_formatter": "formatter",
        "to_analyst": "analyst"  # NUEVO: Vía rápida de vuelta al Cerebro
    }
)

# Después de ejecutar las tools, volvemos DIRECTAMENTE al analista (Tu gran idea)
# workflow.add_edge("tools", "analyst")

# El Formatter es el último paso
workflow.add_edge("formatter", END)

# Compilamos el grafo
workflow_app = workflow.compile()

print("\n[OK] Grafo de LangGraph compilado correctamente.")