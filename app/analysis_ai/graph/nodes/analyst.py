import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from app.analysis_ai.graph.llm_factory import get_gemini_llm

from app.analysis_ai.graph.state import AgentState
from app.analysis_ai.graph.prompts import ANALYST_SYSTEM_PROMPT
from app.analysis_ai.graph.graph_config import GraphConfig

logger = logging.getLogger(__name__)


async def analyst_node(state: AgentState, config: RunnableConfig) -> dict:
    notifier = GraphConfig.get_notifier(config)
    iteration = state.get("iteration_count", 0)

    await notifier.send_log(
        f"[ANALYST AGENT] Processing telemetry (Iteration {iteration})..."
    )

    messages = [SystemMessage(content=ANALYST_SYSTEM_PROMPT)]

    initial_text = (
        f"### SYSTEM DATA TO ANALYZE ###\n"
        f"{state['system_data']}\n\n"
        f"Review this information step by step. Report findings or request tools."
    )
    messages.append(HumanMessage(content=initial_text))

    for msg in state.get("history", []):
        if msg["role"] == "analyst":
            messages.append(AIMessage(content=msg["content"]))
        else:
            messages.append(HumanMessage(content=msg["content"]))

    # Enforce HumanMessage as the final message for Gemini API
    if not isinstance(messages[-1], HumanMessage):
        messages.append(
            HumanMessage(
                content="Continue analysis. Explicitly state 'Analysis finished' if done, or request tools."
            )
        )

    try:
        llm_analyst = get_gemini_llm(temperature=0.2)
        response = await llm_analyst.ainvoke(messages)
        response_text = response.content
    except Exception as e:
        logger.error(f"Analyst LLM Exception: {str(e)}", exc_info=True)
        response_text = "Critical LLM connection error. Analysis terminated."
        await notifier.send_error("LLM connection failed.")
        raise RuntimeError("Critical LLM connection error. Analysis aborted.")

    return {
        "history": [{"role": "analyst", "content": response_text}],
        "iteration_count": iteration + 1,
    }
