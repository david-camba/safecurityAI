import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from .schemas import FeatureSuggestion, FeatureSuggestionsResponse

logger = logging.getLogger(__name__)

# Regex: [YYYY-MM-DD HH:MM:SS] FEATURE: <text> | REASON: <text>
LOG_SUGGESTIONS_PATTERN = re.compile(
    r"^\[(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\]\s+"
    r"FEATURE:\s+(?P<feature>.*?)\s+\|\s+"
    r"REASON:\s+(?P<reason>.*)$"
)


class SuggestionsService:
    """
    Manages the lifecycle of agent feature suggestions,
    including persistence and structured retrieval.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path

    def write_suggestion(self, feature: str, reason: str) -> str:
        """
        Appends a new feature request to the suggestions log.
        Called primarily by the AI Workflow via its dedicated tool.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] FEATURE: {feature} | REASON: {reason}\n"

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
            logger.info(f"Successfully logged feature suggestion: {feature}")
            return "Improvement successfully logged for future iterations."
        except Exception as e:
            logger.error(f"Failed to persist log entry: {str(e)}", exc_info=True)
            raise IOError("Storage failure during feature logging.")

    def get_all_suggestions(self) -> FeatureSuggestionsResponse:
        """
        Parses the suggestion log file and aggregates the entries into a structured response.
        """
        if not self.log_path.exists():
            raise FileNotFoundError("Log file not found.")

        suggestions: List[FeatureSuggestion] = []

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue

                    match = LOG_SUGGESTIONS_PATTERN.match(clean_line)
                    if match:
                        suggestion_data = match.groupdict()
                        suggestions.append(FeatureSuggestion(**suggestion_data))

        except IOError as e:
            logger.error(f"Failed to read suggestions log: {e}", exc_info=True)
            raise IOError("Error reading log file data.")

        return FeatureSuggestionsResponse(
            count=len(suggestions), suggestions=suggestions
        )
