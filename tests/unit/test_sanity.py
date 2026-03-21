def test_environment_is_ready():
    assert True is True


async def test_mock_notifier(mock_notifier):
    await mock_notifier.send_log("Test log")
    assert len(mock_notifier.logs) == 1
    assert mock_notifier.logs[0] == "Test log"
