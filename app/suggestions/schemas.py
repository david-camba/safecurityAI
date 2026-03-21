from pydantic import BaseModel, Field
from typing import List


class FeatureSuggestion(BaseModel):
    date: str = Field(..., description="Formatted date string (YYYY-MM-DD).")
    time: str = Field(..., description="Formatted time string (HH:MM:SS).")
    feature: str = Field(..., description="The requested feature description.")
    reason: str = Field(..., description="The justification or reason for the feature.")


class FeatureSuggestionsResponse(BaseModel):
    count: int
    suggestions: List[FeatureSuggestion]
