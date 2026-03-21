import logging
from langgraph.graph import StateGraph, END

from app.analysis_ai.graph.state import AgentState
from app.analysis_ai.graph.nodes.analyst import analyst_node
from app.analysis_ai.graph.nodes.supporter import supporter_node
from app.analysis_ai.graph.nodes.formatter import formatter_node

logger = logging.getLogger(__name__)


def route_from_supporter(state: AgentState) -> str:
    """
    Evaluates the execution state to determine the next node in the workflow.
    Enforces a strict iteration limit to prevent infinite loops.
    """
    iteration = state.get("iteration_count", 0)

    # 1. Safety mechanism against runaway LLM loops
    if iteration >= 10:
        logger.warning(
            f"Maximum iteration limit ({iteration}) reached. Forcing report generation."
        )
        return "formatter"

    # 2. Controlled exit triggered by the Analyst via the finish_analysis tool
    if state.get("is_finished", False):
        logger.info("Analysis explicitly marked as finished. Routing to formatter.")
        return "formatter"

    # 3. Default continuous analysis loop
    logger.debug("Routing back to Analyst for further evaluation.")
    return "analyst"


# ==========================================
# LANGGRAPH WORKFLOW CONSTRUCTION
# ==========================================

workflow = StateGraph(AgentState)

# Node registration
workflow.add_node("analyst", analyst_node)
workflow.add_node("supporter", supporter_node)
workflow.add_node("formatter", formatter_node)

# Execution flow mapping
workflow.set_entry_point("analyst")

# Analyst always delegates task execution/evaluation to Supporter
workflow.add_edge("analyst", "supporter")

# Supporter evaluates results and routes the workflow
workflow.add_conditional_edges(
    "supporter", route_from_supporter, {"formatter": "formatter", "analyst": "analyst"}
)

# Formatter represents the final stage before termination
workflow.add_edge("formatter", END)

# Compile the asynchronous state graph
workflow_app = workflow.compile()

logger.info("LangGraph workflow compiled successfully.")
