from pydantic import BaseModel, Field
from langchain_core.tools import tool


class FinishInput(BaseModel):
    is_safe: bool = Field(
        description="Set to True if the system is completely safe, or False if threats/anomalies were found."
    )


@tool("finish_analysis", args_schema=FinishInput)
async def finish_analysis(is_safe: bool) -> str:
    """CALL ONLY when the analyst explicitly indicates the entire analysis is finished."""
    return f"Process finished. System safe: {is_safe}"
