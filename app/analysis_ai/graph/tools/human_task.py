from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.analysis_ai.graph.graph_config import GraphConfig


class AskHumanInput(BaseModel):
    questions: List[str] = Field(description="Direct questions or tasks for the user.")


@tool("human_task", args_schema=AskHumanInput)
async def human_task(questions: List[str], config: RunnableConfig) -> str:
    """Requests manual verification or input from the human user."""
    notifier = GraphConfig.get_notifier(config)

    responses = []
    for q in questions:
        await notifier.send_log(f"Awaiting manual intervention: {q}")
        response = await notifier.ask_human(q)
        responses.append(f"Question: {q}\nResponse: {response}")

    return "\n\n".join(responses)
