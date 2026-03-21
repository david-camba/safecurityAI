import pytest
from app.reports.services import ReportsService


@pytest.fixture
def valid_audit_payload():
    return {
        "system_data": '{"os": "Windows 11"}',
        "history": [{"role": "analyst", "content": "Suspicious process found."}],
        "iteration_count": 2,
        "is_finished": True,
        "tool_requests": [],
        "final_report": "# Forensic Analysis\nEverything is secure.",
        "is_system_safe": True,
    }


def test_save_audit_log(temp_logs_dir, valid_audit_payload):
    # Arrange
    service = ReportsService(logs_dir=temp_logs_dir)

    # Act
    report_data = service.save_audit_log(valid_audit_payload)

    # Assert
    assert report_data.is_system_safe is True
    assert report_data.iteration_count == 2

    generated_files = list(temp_logs_dir.glob("audit_report_*.md"))
    assert len(generated_files) == 1

    file_path = generated_files[0]
    assert "safe.md" in file_path.name

    content = file_path.read_text(encoding="utf-8")
    assert "# Forensic Analysis" in content
    assert "<!-- END-OF-REPORT -->" in content
    assert "[ANALYST]" in content


def test_save_audit_log_validation_error(temp_logs_dir):
    # Arrange
    service = ReportsService(logs_dir=temp_logs_dir)
    invalid_payload = {"missing": "required_fields"}

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid audit data format"):
        service.save_audit_log(invalid_payload)


def test_get_all_reports(temp_logs_dir, valid_audit_payload):
    # Arrange
    service = ReportsService(logs_dir=temp_logs_dir)

    service.save_audit_log(valid_audit_payload)

    import time

    time.sleep(1)

    valid_audit_payload["is_system_safe"] = False
    service.save_audit_log(valid_audit_payload)

    # Act
    response = service.get_all_reports()

    # Assert
    assert response.total_count == 2
    assert len(response.reports) == 2

    # Verify sorting (newest first)
    statuses = [report.status for report in response.reports]
    assert set(statuses) == {"safe", "infected"}
    assert statuses[0] == "infected"
    assert statuses[1] == "safe"

    # Validate parsed filename fields
    assert len(response.reports[0].date) == 10  # YYYY-MM-DD
    assert len(response.reports[0].time) == 8  # HH:MM:SS


def test_get_report_by_filename(temp_logs_dir, valid_audit_payload):
    # Arrange
    service = ReportsService(logs_dir=temp_logs_dir)
    service.save_audit_log(valid_audit_payload)

    generated_file = list(temp_logs_dir.glob("audit_report_*.md"))[0]

    # Act
    detail = service.get_report_by_filename(generated_file.name)

    # Assert
    assert detail is not None
    assert "# Forensic Analysis" in detail.content
    assert "Everything is secure." in detail.content

    # Ensure boundary enforcement (metadata should not be in the final output)
    assert "EXECUTION METADATA" not in detail.content
    assert "<!-- END-OF-REPORT -->" not in detail.content


def test_get_report_by_filename_not_found(temp_logs_dir):
    # Arrange
    service = ReportsService(logs_dir=temp_logs_dir)

    # Act
    detail = service.get_report_by_filename("audit_report_20990101_120000_safe.md")

    # Assert
    assert detail is None
