import pytest
from app.suggestions.services import SuggestionsService


def test_write_suggestion(temp_suggestions_file):
    # Arrange
    service = SuggestionsService(log_path=temp_suggestions_file)
    feature = "Network Isolation"
    reason = "Prevent lateral movement during analysis."

    # Act
    result = service.write_suggestion(feature, reason)

    # Assert
    assert result == "Improvement successfully logged for future iterations."
    assert temp_suggestions_file.exists()

    content = temp_suggestions_file.read_text(encoding="utf-8")
    assert "FEATURE: Network Isolation" in content
    assert "REASON: Prevent lateral movement" in content


def test_get_all_suggestions(temp_suggestions_file):
    # Arrange
    service = SuggestionsService(log_path=temp_suggestions_file)
    service.write_suggestion("Feature A", "Reason A")
    service.write_suggestion("Feature B", "Reason B")

    # Act
    response = service.get_all_suggestions()

    # Assert
    assert response.count == 2
    assert len(response.suggestions) == 2

    first_suggestion = response.suggestions[0]
    assert first_suggestion.feature == "Feature A"
    assert first_suggestion.reason == "Reason A"
    # Validating timestamp format indirectly by ensuring regex matched
    assert len(first_suggestion.date) == 10  # YYYY-MM-DD
    assert len(first_suggestion.time) == 8  # HH:MM:SS


def test_get_all_suggestions_file_not_found(temp_suggestions_file):
    # Arrange
    missing_file = temp_suggestions_file.parent / "non_existent.log"
    service = SuggestionsService(log_path=missing_file)

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="Log file not found."):
        service.get_all_suggestions()
