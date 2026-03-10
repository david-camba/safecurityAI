from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import FORMATTER_SYSTEM_PROMPT
from state import AgentState

# Inicializamos el modelo (Gemini Flash es suficiente para redactar, o Pro si quieres máxima calidad)
# Usaremos temperature=0.3 para que sea un poco creativo en la redacción, pero sin alucinar.
formatter_llm = ChatGoogleGenerativeAI(
    model="models/gemini-3.1-flash-lite-preview", 
    temperature=0.4 # Un poco más de temperatura para que redacte bonito
)

def formatter_node(state: AgentState):
    print("\n--- [NODO] FORMATTER (Redactando Informe Final) ---")
    
    # 1. Recopilamos todos los apuntes del Analista
    # Filtramos el historial para pasarle solo lo relevante (lo que pensó el analista y lo que devolvieron las tools)
    apuntes_brutos = ""
    for msg in state.get("history", []):
        rol = msg.get("role", "Desconocido")
        contenido = msg.get("content", "")
        apuntes_brutos += f"[{rol.upper()}]:\n{contenido}\n\n"
        
    # Si por algún motivo el historial está vacío
    if not apuntes_brutos.strip():
        apuntes_brutos = "No hay apuntes del analista. El análisis falló o se interrumpió."

    # 2. Preparamos los mensajes para el LLM
    mensajes = [
        SystemMessage(content=FORMATTER_SYSTEM_PROMPT),
        HumanMessage(content=f"Aquí tienes los apuntes brutos de la sesión de análisis. Redacta el informe final:\n\n{apuntes_brutos}")
    ]
    
    # 3. Invocamos a Gemini
    print("   ✍️ Generando Markdown profesional...")
    respuesta = formatter_llm.invoke(mensajes)
    
    # 4. Actualizamos la variable 'final_report' del State
    return {
        "final_report": respuesta.content
    }