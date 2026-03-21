import pytest
from pathlib import Path
from typing import List

from app.analysis_ai.services.notifier import BaseNotifier


class MockNotifier(BaseNotifier):
    """
    Mock Notifier implementation that stores messages in lists
    for verification within test cases.
    """

    def __init__(self):
        self.logs: List[str] = []
        self.errors: List[str] = []
        self.completions: List[str] = []
        self.human_questions: List[str] = []
        # Configurable simulated response for human interaction tests
        self.mock_human_answer: str = "Simulated human response"

    async def send_log(self, message: str) -> None:
        self.logs.append(message)

    async def ask_human(self, question: str) -> str:
        self.human_questions.append(question)
        return self.mock_human_answer

    async def send_error(self, message: str) -> None:
        self.errors.append(message)

    async def send_completion(self, report: str) -> None:
        self.completions.append(report)


@pytest.fixture
def mock_notifier():
    """Provides a fresh MockNotifier instance for each test."""
    return MockNotifier()


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    """Creates a temporary directory that is automatically removed after the test."""
    logs_dir = tmp_path / "test_logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def temp_suggestions_file(tmp_path: Path) -> Path:
    """Provides a temporary file path for SuggestionsService testing."""
    file_path = tmp_path / "test_suggestions.log"
    return file_path
