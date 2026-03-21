import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.analysis_ai.graph.llm_factory import get_gemini_llm

from app.analysis_ai.graph.state import AgentState
from app.analysis_ai.graph.prompts import FORMATTER_SYSTEM_PROMPT
from app.analysis_ai.graph.graph_config import GraphConfig

logger = logging.getLogger(__name__)


async def formatter_node(state: AgentState, config: RunnableConfig) -> dict:
    notifier = GraphConfig.get_notifier(config)

    await notifier.send_log(
        "[GHOSTWRITER AGENT] Colleting data and generating final forensic report..."
    )

    raw_notes = ""
    for msg in state.get("history", []):
        role = msg.get("role", "UNKNOWN").upper()
        content = msg.get("content", "")
        raw_notes += f"[{role}]:\n{content}\n\n"

    if not raw_notes.strip():
        raw_notes = "No reasoning history available. Analysis interrupted."

    messages = [
        SystemMessage(content=FORMATTER_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Compile the final report based on these logs:\n\n{raw_notes}"
        ),
    ]

    llm_formatter = get_gemini_llm(temperature=0.4)
    response = await llm_formatter.ainvoke(messages)

    await notifier.send_log("Report generation finalized.")

    return {"final_report": response.content}
