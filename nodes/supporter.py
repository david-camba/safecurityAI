from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts import SUPPORTER_PROMPT
from tools import human_task, log_improvement, check_hash_circl, finish_analysis
from state import AgentState

# Metemos todas las tools en una lista y creamos un diccionario para ejecutarlas fácil
TOOLS_LIST = [check_hash_circl, human_task, log_improvement, finish_analysis]
TOOLS_DICT = {tool.name: tool for tool in TOOLS_LIST}

# LLM Base
base_llm = ChatGoogleGenerativeAI(
    model="models/gemini-3.1-flash-lite-preview",
    temperature=0.0,
    max_retries=3
)

# VINCULACIÓN NATIVA
supporter_llm = base_llm.bind_tools(TOOLS_LIST)

def supporter_node(state: AgentState):
    """
    EL ENRUTADOR: Lee el último mensaje del Analista y ejecuta llamadas a funciones nativas.
    """
    print("\n--- [NODO] SUPPORTER (Leyendo intenciones del Analista y ejecutando) ---")
    
    ultimo_mensaje_analista = ""
    if state["history"] and state["history"][-1]["role"] == "analyst":
        ultimo_mensaje_analista = state["history"][-1]["content"]
    
    if not ultimo_mensaje_analista:
        return {"is_finished": False}

    mensajes = [
        SystemMessage(content=SUPPORTER_PROMPT),
        HumanMessage(content=f"Último mensaje del Analista:\n{ultimo_mensaje_analista}")
    ]

    # Invocamos al modelo
    ai_msg = supporter_llm.invoke(mensajes)
    
    is_finished = False
    
    # === AQUI ESTÁ LA CLAVE QUE FALTABA ===
    # Preparamos el string donde concatenaremos los resultados para el Analista
    resultados_texto = "RESULTADOS DE LAS ACCIONES SOLICITADAS:\n\n"
    hubo_ejecucion = False

    if ai_msg.tool_calls:
        print(f"   * Herramientas invocadas: {len(ai_msg.tool_calls)}")
        hubo_ejecucion = True
        
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"     -> Ejecutando: {tool_name} | Args: {tool_args}")
            
            resultados_texto += f"🔹 HERRAMIENTA EJECUTADA: {tool_name}\n"
            
            if tool_name == "finish_analysis":
                is_finished = True
                resultados_texto += "RESULTADO:\nEl análisis ha sido marcado como finalizado.\n\n"
                continue # finish_analysis no necesita ejecución compleja
                
            if tool_name in TOOLS_DICT:
                tool_function = TOOLS_DICT[tool_name]
                try:
                    # Ejecutamos la herramienta
                    tool_result = tool_function.invoke(tool_args)
                    resultados_texto += f"RESULTADO:\n{tool_result}\n\n"
                except Exception as e:
                    # Si falla CIRCL o cualquier otra, el Analista debe saberlo
                    resultados_texto += f"ERROR CRÍTICO EN LA HERRAMIENTA:\n{str(e)}\n\n"
            else:
                resultados_texto += "ERROR: La herramienta no existe en el sistema.\n\n"
    else:
        print("   * Ninguna herramienta invocada. (Pasa turno / razonamiento interno)")

    # Preparamos lo que vamos a devolver para actualizar el State de LangGraph
    state_update = {"is_finished": is_finished}

    # Si se ejecutó alguna herramienta, AÑADIMOS EL RESULTADO AL HISTORIAL
    if hubo_ejecucion:
        nuevo_mensaje_historial = {
            "role": "tool_results", 
            "content": resultados_texto
        }
        # LangGraph usará operator.add y el Analista lo leerá en la siguiente iteración
        state_update["history"] = [nuevo_mensaje_historial]

    return state_update