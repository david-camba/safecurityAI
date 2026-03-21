from fastapi.testclient import TestClient

from app.main import app
from app.analysis_ai.services.ai_workflow import AIWorkflow
from app.reports.services import ReportsService
from app.suggestions.services import SuggestionsService
from app.reports.schemas import ReportsListResponse, ReportItem, ReportDetailResponse
from app.suggestions.schemas import FeatureSuggestionsResponse, FeatureSuggestion

client = TestClient(app)

# ==========================================
# 1. REST API ENDPOINTS
# ==========================================


def test_get_reports_api(mocker):
    # Arrange
    mock_response = ReportsListResponse(
        reports=[
            ReportItem(
                filename="audit_1.md", date="2025-01-01", time="12:00:00", status="safe"
            )
        ],
        total_count=1,
    )
    mocker.patch.object(ReportsService, "get_all_reports", return_value=mock_response)

    # Act
    response = client.get("/api/reports")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["reports"][0]["filename"] == "audit_1.md"


def test_get_suggestions_api(mocker):
    # Arrange
    mock_response = FeatureSuggestionsResponse(
        count=1,
        suggestions=[
            FeatureSuggestion(
                date="2025-01-01",
                time="12:00:00",
                feature="UI Dark Mode",
                reason="Eye strain",
            )
        ],
    )
    mocker.patch.object(
        SuggestionsService, "get_all_suggestions", return_value=mock_response
    )

    # Act
    response = client.get("/api/features")

    # Assert
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_get_report_detail_api_validation_and_404(mocker):
    """
    Ensures the strict Regex validation on the filename path parameter blocks
    invalid formats (preventing Path Traversal attacks) and correctly handles 404s.
    """
    # 1. Test 404 Not Found
    mocker.patch.object(ReportsService, "get_report_by_filename", return_value=None)

    valid_format_name = "audit_report_20250101_120000_safe.md"
    response_404 = client.get(f"/api/reports/{valid_format_name}")
    assert response_404.status_code == 404
    assert response_404.json()["detail"] == "Report not found."

    # 2. Test 422 Unprocessable Entity (Regex mismatch)
    # This proves your regex r"^audit_report_\d{8}_\d{6}_.+\.md$" is working
    invalid_format_name = "malicious_script.sh"
    response_422 = client.get(f"/api/reports/{invalid_format_name}")
    assert response_422.status_code == 422
    assert "string_pattern_mismatch" in response_422.text

    # 3. Test 200 OK (Happy path)
    mock_detail = ReportDetailResponse(
        content="# Safe", date="2025-01-01", time="12:00:00"
    )
    mocker.patch.object(
        ReportsService, "get_report_by_filename", return_value=mock_detail
    )
    response_200 = client.get(f"/api/reports/{valid_format_name}")
    assert response_200.status_code == 200
    assert response_200.json()["content"] == "# Safe"


# ==========================================
# 2. WEBSOCKET BIDIRECTIONAL COMMUNICATION
# ==========================================


def test_websocket_analyze_happy_path(mocker):
    """
    Simulates a complete WebSocket session:
    1. Client connects.
    2. Server streams logs.
    3. Server interrupts workflow to ask the human a question.
    4. Client responds successfully.
    5. Server completes the workflow and sends the final report.
    """

    # 1. MOCK THE WORKFLOW BEHAVIOR
    async def mock_run_analysis(notifier):
        # Simulate initial telemetry log
        await notifier.send_log("Booting AI Core...")

        # Simulate the LLM triggering the 'human_task' tool
        human_resp = await notifier.ask_human(
            "Do you recognize this suspicious process?"
        )
        assert (
            human_resp == "Yes, it is my VPN."
        )  # Verify the notifier captured the client's payload

        # Return a mocked valid LangGraph terminal state
        return {
            "system_data": "",
            "history": [],
            "iteration_count": 2,
            "is_finished": True,
            "tool_requests": [],
            "final_report": "# Final Report\nSystem is secure.",
            "is_system_safe": True,
        }

    # Patch the workflow execution and the file system persistence
    mocker.patch.object(AIWorkflow, "run_analysis", side_effect=mock_run_analysis)

    # Mock save_audit_log to return a fake created schema instead of writing to disk
    from app.reports.schemas import AuditReportCreate

    mock_saved_report = AuditReportCreate(
        system_data="", final_report="# Final Report\nSystem is secure."
    )
    mocker.patch.object(
        ReportsService, "save_audit_log", return_value=mock_saved_report
    )

    # 2. EXECUTE THE WEBSOCKET CONNECTION
    with client.websocket_connect("/ws/analyze") as websocket:
        # A. Expect initial log message
        log_msg = websocket.receive_json()
        assert log_msg["type"] == "log"
        assert log_msg["content"] == "Booting AI Core..."

        # B. Expect the human intervention request
        action_msg = websocket.receive_json()
        assert action_msg["type"] == "action_request"
        assert action_msg["action_type"] == "text_input"
        assert "recognize this suspicious process" in action_msg["message"]

        # C. Client sends the response back to the server
        websocket.send_json(
            {"type": "human_text_answer", "answer": "Yes, it is my VPN."}
        )

        # D. Expect the server to acknowledge receipt of the action
        ack_msg = websocket.receive_json()
        assert ack_msg["type"] == "action_ack"

        # E. Expect final completion payload
        completion_msg = websocket.receive_json()
        assert completion_msg["type"] == "complete"
        assert "System is secure." in completion_msg["report"]


def test_websocket_analyze_handles_critical_errors(mocker):
    """
    Ensures that if the AI Workflow encounters a fatal exception
    (e.g., LLM disconnects, PowerShell fails), the WebSocket gracefully
    catches it, informs the client via an 'error' packet, and closes safely.
    """

    # Arrange: Force the workflow to crash immediately
    mocker.patch.object(
        AIWorkflow,
        "run_analysis",
        side_effect=RuntimeError("Google Gemini API is unreachable."),
    )

    # Act
    with client.websocket_connect("/ws/analyze") as websocket:
        # Assert: The router's try/except block should catch the error and dispatch it
        error_msg = websocket.receive_json()

        assert error_msg["type"] == "error"
        assert "Google Gemini API is unreachable." in error_msg["content"]


def test_websocket_recovers_from_invalid_client_payload(mocker):
    """
    Proves the system's fault tolerance: If the connected client sends a malformed
    JSON while the AI is waiting for a human answer, the server must NOT crash.
    It should reject the payload, notify the client, and continue waiting.
    """

    # Arrange
    async def mock_run_analysis(notifier):
        # The workflow asks a question and pauses
        answer = await notifier.ask_human("Please confirm.")
        # We assert that it eventually receives the correct answer
        assert answer == "Valid response finally sent."

        # Required return structure to satisfy the ReportsService Anti-Corruption Layer
        from app.reports.schemas import AuditReportCreate

        return AuditReportCreate(
            system_data="", final_report="Done.", is_system_safe=True
        ).model_dump()

    mocker.patch.object(AIWorkflow, "run_analysis", side_effect=mock_run_analysis)

    from app.reports.schemas import AuditReportCreate

    mock_saved_report = AuditReportCreate(
        system_data="", final_report="Done.", is_system_safe=True
    )
    mocker.patch.object(
        ReportsService, "save_audit_log", return_value=mock_saved_report
    )

    # Act & Assert
    with client.websocket_connect("/ws/analyze") as websocket:
        # 1. Server asks the question
        action_msg = websocket.receive_json()
        assert action_msg["type"] == "action_request"

        # 2. MALICIOUS/BUGGY CLIENT ACTION: Send an invalid Pydantic payload
        websocket.send_json({"type": "wrong_type", "garbage_data": 123})

        # 3. Server gracefully catches ValidationError and sends an error frame back
        error_msg = websocket.receive_json()
        assert error_msg["type"] == "error"
        assert "Invalid payload format" in error_msg["content"]

        # 4. CORRECT CLIENT ACTION: The client fixes its mistake and sends valid data
        websocket.send_json(
            {"type": "human_text_answer", "answer": "Valid response finally sent."}
        )

        # 5. Server accepts it, acks, and finishes the workflow
        ack_msg = websocket.receive_json()
        assert ack_msg["type"] == "action_ack"

        completion_msg = websocket.receive_json()
        assert completion_msg["type"] == "complete"
