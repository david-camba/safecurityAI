import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.analysis_ai.graph.llm_factory import get_gemini_llm

from app.analysis_ai.graph.state import AgentState
from app.analysis_ai.graph.prompts import SUPPORTER_PROMPT
from app.analysis_ai.graph.graph_config import GraphConfig
from app.analysis_ai.graph.tools import (
    human_task,
    log_improvement,
    check_hash_circl,
    finish_analysis,
)

logger = logging.getLogger(__name__)

# The Supporter Node is the HANDS of the workflow
# Translates the Analyzer requests into tool calls
TOOLS_LIST = [check_hash_circl, human_task, log_improvement, finish_analysis]
TOOLS_DICT = {tool.name: tool for tool in TOOLS_LIST}


async def supporter_node(state: AgentState, config: RunnableConfig) -> dict:
    notifier = GraphConfig.get_notifier(config)

    await notifier.send_log("[SUPPORTER AGENT] Evaluating analytical requirements...")

    last_analyst_msg = state["history"][-1]["content"] if state.get("history") else ""
    if not last_analyst_msg:
        return {"is_finished": False}

    messages = [
        SystemMessage(content=SUPPORTER_PROMPT),
        HumanMessage(content=f"Latest Analyst message:\n{last_analyst_msg}"),
    ]

    supporter_llm = get_gemini_llm(temperature=0.0).bind_tools(TOOLS_LIST)
    ai_msg = await supporter_llm.ainvoke(messages)

    is_finished = False
    is_system_safe = None
    results_text = "REQUESTED ACTION RESULTS:\n\n"
    executed_any = False

    if ai_msg.tool_calls:
        executed_any = True
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"Dispatching tool execution: {tool_name}")
            results_text += f"🔹 EXECUTED TOOL: {tool_name}\n"

            # Intercept and process finish_analysis
            if tool_name == "finish_analysis":
                is_finished = True
                is_system_safe = tool_args.get("is_safe", False)
                results_text += f"RESULT: Analysis marked as complete. System safe: {is_system_safe}\n\n"
                continue

            if tool_name in TOOLS_DICT:
                tool_function = TOOLS_DICT[tool_name]
                try:
                    # Propagate config downstream to ensure tools can extract the notifier
                    tool_result = await tool_function.ainvoke(tool_args, config)
                    results_text += f"RESULT:\n{tool_result}\n\n"
                except Exception as e:
                    logger.error(f"Execution failure in {tool_name}: {str(e)}")
                    results_text += f"CRITICAL TOOL ERROR:\n{str(e)}\n\n"
            else:
                results_text += "ERROR: Tool reference not found in registry.\n\n"

    state_update = {"is_finished": is_finished}

    if is_system_safe is not None:
        state_update["is_system_safe"] = is_system_safe

    if executed_any:
        state_update["history"] = [{"role": "tool_results", "content": results_text}]
    else:
        state_update["history"] = [
            {
                "role": "tool_results",
                "content": "SYSTEM: No tools were executed.",
            }
        ]

    return state_update
