import logging
from app.analysis_ai.graph.state import AgentState

from app.analysis_ai.services.notifier import BaseNotifier

from app.analysis_ai.services.windows_scanner import run_local_scan

from app.analysis_ai.graph.graph import workflow_app
from app.analysis_ai.graph.graph_config import GraphConfig


logger = logging.getLogger(__name__)


class AIWorkflow:
    """Orchestrates the Security Analysis using LangGraph."""

    async def run_analysis(self, notifier: BaseNotifier) -> AgentState:
        # 1. Fail-fast dependency injection
        config = GraphConfig.set_notifier(notifier)

        await notifier.send_log(
            "Initializing local telemetry collection, be patient, this can last a few minutes..."
        )
        system_data = await run_local_scan(notifier=notifier)
        await notifier.send_log("Telemetry collected successfully. Booting AI Core...")

        initial_state = AgentState(
            system_data=system_data,
            history=[],
            iteration_count=0,
            is_finished=False,
            tool_requests=[],
            final_report="",
            is_system_safe=False,
        )

        await notifier.send_log("AI Analysis in progress. Please hold...")

        # Graph execution
        final_state = await workflow_app.ainvoke(initial_state, config=config)
        return final_state
