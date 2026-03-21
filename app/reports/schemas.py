from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Literal


def _normalize_llm_output(value: Any) -> str:
    """Extract plain text if the LLM returns a list of JSON blocks."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in value
        )
    return str(value) if value is not None else ""


# ==========================================
# REPORT CREATION CONTRACT (Used by Analysis AI to pass data here)
# ==========================================
class AuditReportCreate(BaseModel):
    system_data: str
    history: List[Dict[str, Any]] = Field(default_factory=list)
    iteration_count: int = 0
    is_finished: bool = False
    tool_requests: List[Dict[str, Any]] = Field(default_factory=list)
    final_report: str
    is_system_safe: bool = False

    @field_validator("final_report", mode="before")
    @classmethod
    def force_string_report(cls, v: Any) -> str:
        return _normalize_llm_output(v)

    @field_validator("history", mode="before")
    @classmethod
    def clean_history_content(cls, v: Any) -> List[Dict[str, Any]]:
        if not isinstance(v, list):
            return v

        cleaned_history = []
        for msg in v:
            if isinstance(msg, dict) and "content" in msg:
                new_msg = msg.copy()
                new_msg["content"] = _normalize_llm_output(msg["content"])
                cleaned_history.append(new_msg)
            else:
                cleaned_history.append(msg)
        return cleaned_history


# ==========================================
# REPORT RETRIEVAL CONTRACTS (API Responses)
# ==========================================
class ReportItem(BaseModel):
    filename: str
    date: str
    time: str
    status: Literal["safe", "infected"]


class ReportsListResponse(BaseModel):
    reports: List[ReportItem] = Field(default_factory=list)
    total_count: int = Field(default=0)


class ReportDetailResponse(BaseModel):
    content: str
    date: str
    time: str
