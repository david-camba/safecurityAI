import pytest
import respx
import httpx
from app.analysis_ai.graph.tools.hashlookup_api import check_hash_circl
from app.analysis_ai.graph.graph_config import GraphConfig


@pytest.fixture
def graph_config(mock_notifier):
    """Generates a valid LangGraph RunnableConfig with the injected Notifier."""
    return GraphConfig.set_notifier(mock_notifier)


@respx.mock
async def test_check_hash_circl_found(graph_config, mock_notifier):
    # Arrange
    valid_hash = (
        "d14a028c2a3a2bc947cefd47d519b78cb47d96cc3792bce9bc98db5f573fc08a"  # 64 chars
    )
    mock_url = f"https://hashlookup.circl.lu/lookup/sha256/{valid_hash}"

    # Intercept the exact URL and return a fake 200 JSON response
    respx.get(mock_url).mock(
        return_value=httpx.Response(
            200, json={"FileName": "explorer.exe", "ProductName": "Microsoft Windows"}
        )
    )

    # Act
    result = await check_hash_circl.ainvoke(
        {"hashes": [valid_hash]}, config=graph_config
    )

    # Assert
    assert "FOUND" in result
    assert "explorer.exe" in result
    assert "Microsoft Windows" in result
    assert len(mock_notifier.logs) > 0  # Verify notifier was utilized


@respx.mock
async def test_check_hash_circl_not_found(graph_config):
    # Arrange
    unknown_hash = "a" * 64
    mock_url = f"https://hashlookup.circl.lu/lookup/sha256/{unknown_hash}"

    respx.get(mock_url).mock(return_value=httpx.Response(404))

    # Act
    result = await check_hash_circl.ainvoke(
        {"hashes": [unknown_hash]}, config=graph_config
    )

    # Assert
    assert "NOT FOUND in database" in result


async def test_check_hash_circl_invalid_format(graph_config):
    # Arrange
    invalid_hash = "too_short"

    # Act - HTTP mock not needed as pre-flight validation should block it
    result = await check_hash_circl.ainvoke(
        {"hashes": [invalid_hash]}, config=graph_config
    )

    # Assert
    assert "Invalid format" in result


@respx.mock
async def test_check_hash_circl_timeout(graph_config):
    # Arrange
    valid_hash = "b" * 64
    mock_url = f"https://hashlookup.circl.lu/lookup/sha256/{valid_hash}"

    # Simulate a network timeout exception
    respx.get(mock_url).mock(side_effect=httpx.RequestError("Mocked Timeout"))

    # Act
    result = await check_hash_circl.ainvoke(
        {"hashes": [valid_hash]}, config=graph_config
    )

    # Assert
    assert "Network timeout or request error" in result
    assert "Mocked Timeout" in result
