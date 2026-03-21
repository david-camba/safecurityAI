# DEPRECATED
# If we want to use a really cheap model as Supporter Node, we could translate the response of an LLM without tooling support into a JSON and use this node to parse it and execute the Analyzer requests.
# It could make the workflow more fragile, but potentially cheaper

from app.analysis_ai.graph.tools import human_task, log_improvement, check_hash_circl
from app.analysis_ai.graph.state import AgentState


def tool_execution_node(state: AgentState):
    print("\n--- [NODE] TOOL EXECUTION (Executing actions) ---")

    requests = state.get("tool_requests", [])

    # If no requests are found, return empty update
    if not requests:
        return {}

    # Maps LLM request strings to Python functions
    tool_map = {
        "human_task": human_task.invoke,
        "log_improvement": log_improvement.invoke,
        "check_hash_circl": check_hash_circl.invoke,
    }

    # Concatenate results in plain text for analyst evaluation
    resultados_texto = "ACTION EXECUTION RESULTS:\n\n"

    for req in requests:
        nombre_tool = req.get("tool_name")
        argumentos = req.get("args", {})

        print(f"   ⚙️ Executing: {nombre_tool}...")
        resultados_texto += f"🔹 TOOL EXECUTED: {nombre_tool}\n"

        try:
            funcion_real = tool_map.get(nombre_tool)

            if funcion_real:
                # Execute tool with provided arguments
                resultado = funcion_real(argumentos)
                resultados_texto += f"RESULT:\n{resultado}\n\n"
                print("      [OK] Execution completed.")
            else:
                error_msg = (
                    f"Error: Tool '{nombre_tool}' is not registered in the system."
                )
                resultados_texto += f"{error_msg}\n\n"
                print(f"      [ERROR] {error_msg}")

        except Exception as e:
            # Critical: Ensure system resiliency if external APIs (e.g. CIRCL) fail.
            # Log exception for Analyst review.
            error_trace = f"Exception during execution: {str(e)}"
            resultados_texto += f"CRITICAL TOOL ERROR:\n{error_trace}\n\n"
            print(f"      [FAILURE] {error_trace}")

    # Package response as a tool_results message for conversation history
    nuevo_mensaje_historial = {"role": "tool_results", "content": resultados_texto}

    # LangGraph will append this to 'history' via operator.add
    return {"history": [nuevo_mensaje_historial]}
