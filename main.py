import os
from datetime import datetime
from dotenv import load_dotenv

# ===================================================================
# 0. CONFIGURACIÓN Y AUTENTICACIÓN
# ===================================================================
# Cargar variables de entorno desde el archivo .env ANTES de importar LangGraph
load_dotenv()

# Validar que la API Key existe para no fallar a mitad de proceso
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ ERROR CRÍTICO: No se ha encontrado la variable GOOGLE_API_KEY.")
    print("Por favor, crea un archivo '.env' en este directorio y añade:")
    print("GOOGLE_API_KEY='tu_clave_de_gemini_aqui'")
    exit(1)

# Ahora sí importamos el resto de nuestros módulos
from windows_scanner import run_local_scan
# Importamos la app compilada (asegúrate de que en graph.py la compilación se llame workflow_app)
from graph import workflow_app 

def save_audit_log(state: dict):
    """
    Guarda TODO el estado de LangGraph en un archivo Markdown dentro de 'logs'.
    Incluye el reporte, metadatos, el historial completo de pensamiento y los datos del sistema.
    """
    os.makedirs("logs", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/audit_report_{timestamp}.md"
    
    with open(log_filename, "w", encoding="utf-8") as f:
        # 1. Reporte Final (Lo que le interesa a Dirección)
        f.write("# 🛡️ REPORTE FINAL DE AUDITORÍA\n\n")
        
        # --- CORRECCIÓN DE TIPOS AQUÍ ---
        report_data = state.get("final_report", "No se generó reporte final.")
        if isinstance(report_data, list):
            # Si LangGraph lo devolvió como lista, unimos los fragmentos
            report_text = "\n\n".join(str(item) for item in report_data)
        else:
            # Si es string u otro objeto, forzamos la conversión a texto
            report_text = str(report_data)
            
        f.write(report_text)
        f.write("\n\n---\n\n")
        
        # 2. Metadatos del Grafo
        f.write("## ⚙️ METADATOS DE EJECUCIÓN (LangGraph)\n")
        f.write(f"- **Total de Iteraciones (Llamadas al Analista):** {state.get('iteration_count', 0)}\n")
        f.write(f"- **Finalizado por el Agente:** {state.get('is_finished', False)}\n")
        
        # Protección extra para las herramientas
        tool_requests = state.get('tool_requests', [])
        if not isinstance(tool_requests, list): 
            tool_requests = []
        f.write(f"- **Últimas herramientas en cola:** {len(tool_requests)}\n")
        f.write("\n---\n\n")

        # 3. El Cerebro: Historial de Razonamiento
        f.write("## 🧠 HISTORIAL DE RAZONAMIENTO Y ACCIONES\n\n")
        history = state.get("history", [])
        if not isinstance(history, list): 
            history = []
            
        if not history:
            f.write("No hay historial registrado.\n")
        else:
            for msg in history:
                if isinstance(msg, dict):
                    role = msg.get("role", "Desconocido").upper()
                    content = msg.get("content", "")
                else:
                    # Por si LangGraph inyectó un objeto BaseMessage directamente
                    role = "MENSAJE_SISTEMA"
                    content = str(msg)
                    
                f.write(f"### [{role}]\n")
                f.write(f"{content}\n\n")
                
        f.write("\n---\n\n")
        
        # 4. Datos Crudos (Colapsables en Markdown)
        f.write("## 💻 DATOS DEL SISTEMA INYECTADOS (RAW)\n")
        f.write("<details>\n<summary>Haz clic para expandir la telemetría del PowerShell</summary>\n\n")
        f.write("```json\n")
        
        # Protección extra para los datos del sistema
        sys_data = state.get("system_data", "No hay datos del sistema.")
        if isinstance(sys_data, list):
            sys_data = "\n".join(str(item) for item in sys_data)
        else:
            sys_data = str(sys_data)
            
        f.write(sys_data)
        f.write("\n```\n")
        f.write("</details>\n")
        
    print(f"\n[💾] Auditoría LangGraph guardada permanentemente en: {log_filename}")


def main():
    print("="*60)
    print("🛡️  MOTOR DE ANÁLISIS FORENSE AUTÓNOMO (LangGraph) 🛡️")
    print("="*60)

    # ---------------------------------------------------------
    # FASE 1: RECOPILACIÓN DE DATOS (El "Sensor")
    # ---------------------------------------------------------
    try:
        system_data = run_local_scan("script_auditoria.ps1")
    except Exception as e:
        print(f"Error Crítico en la recopilación: {e}")
        return

    # ---------------------------------------------------------
    # FASE 2: INYECCIÓN AL GRAFO (El "Cerebro")
    # ---------------------------------------------------------
    print("\n[+] Inyectando telemetría en el Grafo de IA (LangGraph)...")
    
    # Inicializamos el estado base de LangGraph
    initial_state = {
        "system_data": system_data,
        "history": [],
        "iteration_count": 0,
        "is_finished": False,
        "tool_requests": [],
        "final_report": ""
    }

    print("\n🚀 Iniciando ejecución autónoma...")
    
    # LLAMADA REAL AL GRAFO:
    # workflow_app.invoke() ejecuta el grafo y devuelve el diccionario 'state' actualizado al final
    final_state = workflow_app.invoke(initial_state)

    # ---------------------------------------------------------
    # FASE 3: PERSISTENCIA Y SALIDA
    # ---------------------------------------------------------
    print("\n[+] Análisis LangGraph completado con éxito.")
    
    # Guardamos TODO el final_state
    save_audit_log(final_state)

if __name__ == "__main__":
    main()