from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

class AskHumanInput(BaseModel):
    questions: List[str] = Field(
        description="Lista de preguntas o tareas claras y directas para el usuario."
    )

@tool("human_task", args_schema=AskHumanInput)
def human_task(questions: List[str]) -> str:
    """Útil para hacer preguntas al usuario humano o pedirle que realice tareas manuales."""
    print("\n" + "="*50)
    print("🧑‍💻 [INTERVENCIÓN HUMANA REQUERIDA]")
    
    respuestas_humanas = []
    for i, q in enumerate(questions, 1):
        print(f"\n🤖 Pregunta {i}: {q}")
        respuesta = input("📝 Tu respuesta (o 'skip'): ")
        if respuesta.strip().lower() == 'skip':
            respuestas_humanas.append(f"Pregunta: {q} -> Respuesta: [IGNORADA POR EL USUARIO]")
        else:
            respuestas_humanas.append(f"Pregunta: {q} -> Respuesta: {respuesta}")
            
    print("="*50)
    return "\n".join(respuestas_humanas)
