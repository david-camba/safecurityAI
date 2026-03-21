import asyncio
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.analysis_ai.graph.graph_config import GraphConfig
from app.suggestions.services import SuggestionsService


class LogImprovementInput(BaseModel):
    feature: str = Field(description="The action that was attempted but not available.")
    reason: str = Field(description="Why this action is necessary.")


@tool("log_improvement", args_schema=LogImprovementInput)
async def log_improvement(feature: str, reason: str, config: RunnableConfig) -> str:
    """Logs a system limitation or missing capability. Call once per missing feature."""
    notifier = GraphConfig.get_notifier(config)
    await notifier.send_log(f"Logging missing feature request: {feature}")

    service = SuggestionsService()

    try:
        # Offload synchronous file I/O to a background thread
        return await asyncio.to_thread(service.write_suggestion, feature, reason)
    except Exception as e:
        return f"Failed to persist log entry: {str(e)}"
