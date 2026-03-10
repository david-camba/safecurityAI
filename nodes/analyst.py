from state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompts import ANALYST_SYSTEM_PROMPT
from langchain_google_genai import ChatGoogleGenerativeAI

llm_analyst = ChatGoogleGenerativeAI(
    model="models/gemini-3.1-flash-lite-preview", # (Ajusta el string exacto según la API de Google)
    temperature=0.2,
    max_retries=3
)


def analyst_node(state: AgentState):
    print(f"\n--- [NODO] ANALYST (Iteración {state['iteration_count']}) ---")
    
    # 1. Mensaje de Sistema: SOLO la personalidad y las reglas
    mensajes_para_llm = [
        SystemMessage(content=ANALYST_SYSTEM_PROMPT)
    ]
    
    # 2. El primer input del usuario (Humano) SIEMPRE serán los datos crudos
    texto_inicial = (
        f"### DATOS DEL SISTEMA A ANALIZAR ###\n"
        f"{state['system_data']}\n\n"
        f"Por favor, revisa esta información paso a paso. Dime qué encuentras o pide usar herramientas."
    )
    mensajes_para_llm.append(HumanMessage(content=texto_inicial))
    
    # 3. Reconstruimos el historial de la conversación
    for msg in state.get("history", []):
        if msg["role"] == "analyst":
            mensajes_para_llm.append(AIMessage(content=msg["content"]))
        else:
            # Los resultados de las tools entran como HumanMessage
            mensajes_para_llm.append(HumanMessage(content=msg["content"]))
            
    # 4. ⚠️ REGLA DE ORO DE GEMINI: El último mensaje debe ser siempre de un Humano.
    # Si por algún motivo el router nos devolvió aquí sin pasar por una tool, 
    # el último mensaje sería un AIMessage y la API crashearía. Lo prevenimos así:
    if isinstance(mensajes_para_llm[-1], AIMessage):
        mensajes_para_llm.append(HumanMessage(
            content="Continúa con tu análisis. Recuerda que si has terminado debes indicar "
                    "claramente 'Análisis finalizado' o pedir herramientas si ves algo sospechoso."
        ))
            
    # 5. Llamada al LLM Real
    print("   🤖 Analista pensando (procesando reglas y contexto)...")
    try:
        respuesta = llm_analyst.invoke(mensajes_para_llm)
        texto_respuesta = respuesta.content
    except Exception as e:
        print(f"   [ERROR CRÍTICO LLM] {e}")
        texto_respuesta = "Error de conexión con IA. Análisis finalizado."
    
    print(f"   💬 Respuesta IA: {texto_respuesta[:150]}...\n")

    # 6. Actualizamos el estado
    nuevo_historial = {"role": "analyst", "content": texto_respuesta}
    
    return {
        "history": [nuevo_historial], 
        "iteration_count": state["iteration_count"] + 1
    }