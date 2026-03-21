import operator
from typing import TypedDict, List, Annotated, Dict, Any


class AgentState(TypedDict):
    system_data: str  # Tasks, Windows Defender permissions, networks, etc, extracted by the PowerShell script
    history: Annotated[List[Dict[str, Any]], operator.add]
    iteration_count: int
    is_finished: bool
    tool_requests: list
    final_report: str
    is_system_safe: bool
