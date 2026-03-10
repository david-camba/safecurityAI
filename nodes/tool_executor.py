from tools import human_task, log_improvement, check_hash_circl
from state import AgentState

def tool_execution_node(state: AgentState):
    print("\n--- [NODO] TOOL EXECUTION (Ejecutando acciones) ---")
    
    requests = state.get("tool_requests", [])
    
    # Si por algún motivo llegamos aquí sin peticiones, devolvemos un log vacío
    if not requests:
        return {}

    # Diccionario para mapear el string del LLM con la función real de Python
    # NOTA: En LangChain, las funciones decoradas con @tool se ejecutan con .invoke()
    tool_map = {
        "human_task": human_task.invoke,
        "log_improvement": log_improvement.invoke,
        "check_hash_circl": check_hash_circl.invoke
    }

    # Aquí iremos concatenando en texto plano todos los resultados 
    # para que el Analista (El Cerebro) los lea en el siguiente turno.
    resultados_texto = "RESULTADOS DE LAS ACCIONES SOLICITADAS:\n\n"

    for req in requests:
        nombre_tool = req.get("tool_name")
        argumentos = req.get("args", {})
        
        print(f"   ⚙️ Ejecutando: {nombre_tool}...")
        resultados_texto += f"🔹 HERRAMIENTA EJECUTADA: {nombre_tool}\n"
        
        try:
            # Buscamos la función en nuestro diccionario
            funcion_real = tool_map.get(nombre_tool)
            
            if funcion_real:
                # Ejecutamos la herramienta pasándole los argumentos (el JSON del Supporter)
                resultado = funcion_real(argumentos)
                resultados_texto += f"RESULTADO:\n{resultado}\n\n"
                print("      [OK] Ejecución completada.")
            else:
                error_msg = f"Error: La herramienta '{nombre_tool}' no está programada en el sistema."
                resultados_texto += f"{error_msg}\n\n"
                print(f"      [ERROR] {error_msg}")
                
        except Exception as e:
            # Fundamental: Si una API (ej. CIRCL) falla, el sistema NO debe romperse.
            # Capturamos el error y se lo decimos al Analista para que lo sepa.
            error_trace = f"Excepción durante la ejecución: {str(e)}"
            resultados_texto += f"ERROR CRÍTICO EN LA HERRAMIENTA:\n{error_trace}\n\n"
            print(f"      [FALLO] {error_trace}")

    # Empaquetamos todo este texto en un nuevo mensaje para el historial
    nuevo_mensaje_historial = {
        "role": "tool_results", 
        "content": resultados_texto
    }

    # LangGraph detectará que 'history' usa operator.add y concatenará este mensaje al final
    return {
        "history": [nuevo_mensaje_historial]
    }