import pytest
from app.analysis_ai.services.windows_scanner import run_local_scan
from app.config import settings


class MockProcess:
    """
    Simulates a subprocess.Popen object emitting standard output.
    Used to verify that the threading architecture correctly streams data.
    """

    def __init__(self, stdout_lines, returncode=0):
        self.stdout = stdout_lines
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def wait(self):
        # Mocks the synchronous block waiting for process completion
        pass


async def test_run_local_scan_success(mocker, mock_notifier):
    # Arrange
    # Force live execution path regardless of local environment variables
    mocker.patch.object(settings, "DEBUG_ON", False)

    # Bypass OS-level directory and file validations
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.makedirs")

    # Intercept subprocess execution to simulate PowerShell streaming output
    mocker.patch(
        "subprocess.Popen",
        return_value=MockProcess(
            stdout_lines=["Initializing scan...\n", "Extracting processes...\n"],
            returncode=0,
        ),
    )

    # When the service tries to read the final telemetry file, return this string.
    mocker.patch("builtins.open", mocker.mock_open(read_data='{"mocked": "telemetry"}'))

    # Act
    result = await run_local_scan(ps_script_path="dummy.ps1", notifier=mock_notifier)

    # Assert
    # 1. Verify the final payload was successfully retrieved
    assert result == '{"mocked": "telemetry"}'

    # 2. Verify that the cross-thread streaming architecture successfully
    # routed the standard output lines to the WebSocket notifier
    logs = [msg for msg in mock_notifier.logs if "[WINDOWS SCANNER]" in msg]
    assert len(logs) == 2
    assert "Initializing scan..." in logs[0]
    assert "Extracting processes..." in logs[1]


async def test_run_local_scan_debug_mode(mocker, mock_notifier):
    # Arrange
    # Force bypass logic (used for UI development without running telemetry)
    mocker.patch.object(settings, "DEBUG_ON", True)

    # Mock file system searches to simulate finding an old scan
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("glob.glob", return_value=["/fake/path/complete_scan.txt"])
    mocker.patch("os.path.getctime", return_value=1234567890.0)

    # Intercept native open()
    mock_open = mocker.patch(
        "builtins.open", mocker.mock_open(read_data='{"historical": "data"}')
    )

    # Intercept subprocess to ensure it is NEVER called
    mock_popen = mocker.patch("subprocess.Popen")

    # Act
    result = await run_local_scan(notifier=mock_notifier)

    # Assert
    assert result == '{"historical": "data"}'

    # Critical security/performance check: ensure payload was not executed
    mock_popen.assert_not_called()
    mock_open.assert_called_with("/fake/path/complete_scan.txt", "r", encoding="utf-8")


async def test_run_local_scan_process_failure(mocker, mock_notifier):
    # Arrange
    mocker.patch.object(settings, "DEBUG_ON", False)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.makedirs")

    # Simulate a crashed PowerShell execution (non-zero exit code)
    mocker.patch(
        "subprocess.Popen",
        return_value=MockProcess(
            stdout_lines=["Fatal execution policy error\n"], returncode=1
        ),
    )

    # Act & Assert
    # Verify the background thread propagates the error back to the main event loop
    with pytest.raises(RuntimeError, match="Scanner process terminated unexpectedly"):
        await run_local_scan(notifier=mock_notifier)
