import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage

from app.analysis_ai.graph.state import AgentState
from app.analysis_ai.graph.graph_config import GraphConfig
from app.analysis_ai.graph.nodes.analyst import analyst_node
from app.analysis_ai.graph.nodes.supporter import supporter_node
from app.analysis_ai.graph.nodes.formatter import formatter_node


@pytest.fixture
def graph_config(mock_notifier):
    """Provides a valid LangGraph configuration context."""
    return GraphConfig.set_notifier(mock_notifier)


@pytest.fixture
def base_state() -> AgentState:
    """Provides a clean initial state for node execution."""
    return {
        "system_data": '{"os": "Windows", "processes": []}',
        "history": [],
        "iteration_count": 0,
        "is_finished": False,
        "tool_requests": [],
        "final_report": "",
        "is_system_safe": False,
    }


def mock_llm_factory(mocker, module_path: str, mock_response: AIMessage):
    """
    Helper to intercept the LLM factory in a specific module and inject
    an AsyncMock that returns a predefined LangChain AIMessage.
    """
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    # Required for Supporter node which chains .bind_tools() before .ainvoke()
    mock_llm.bind_tools.return_value = mock_llm

    mocker.patch(f"{module_path}.get_gemini_llm", return_value=mock_llm)
    return mock_llm


async def test_analyst_node_success(mocker, base_state, graph_config):
    # Arrange
    expected_response = "I have reviewed the telemetry. Please check hashes."
    mock_llm_factory(
        mocker,
        "app.analysis_ai.graph.nodes.analyst",
        AIMessage(content=expected_response),
    )

    # Act
    result = await analyst_node(base_state, graph_config)

    # Assert
    # 1. State mutations are correct
    assert result["iteration_count"] == 1
    assert len(result["history"]) == 1

    # 2. History payload is properly formatted for LangGraph's operator.add
    history_entry = result["history"][0]
    assert history_entry["role"] == "analyst"
    assert history_entry["content"] == expected_response


async def test_analyst_node_llm_failure(
    mocker, base_state, graph_config, mock_notifier
):
    # Arrange
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Rate Limit"))
    mocker.patch(
        "app.analysis_ai.graph.nodes.analyst.get_gemini_llm", return_value=mock_llm
    )

    # Act & Assert
    # The node is designed to fail fast and bubble up the exception to halt the workflow
    with pytest.raises(RuntimeError, match="Critical LLM connection error"):
        await analyst_node(base_state, graph_config)

    assert "LLM connection failed." in mock_notifier.errors


async def test_supporter_node_executes_tool(mocker, base_state, graph_config):
    # Arrange
    base_state["history"] = [{"role": "analyst", "content": "Check this hash."}]

    # Simulate the LLM deciding to invoke the CIRCL tool
    ai_tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_fake123",
                "name": "check_hash_circl",
                "args": {"hashes": ["fake_hash"]},
            }
        ],
    )
    mock_llm_factory(mocker, "app.analysis_ai.graph.nodes.supporter", ai_tool_call)

    # Intercept the tool execution to prevent actual HTTP requests
    from app.analysis_ai.graph.nodes import supporter

    mock_tool = AsyncMock()
    mock_tool.ainvoke.return_value = "FOUND: fake_malware.exe"
    mocker.patch.dict(supporter.TOOLS_DICT, {"check_hash_circl": mock_tool})

    # Act
    result = await supporter_node(base_state, graph_config)

    # Assert
    assert result["is_finished"] is False
    assert "history" in result

    tool_results_content = result["history"][0]["content"]
    assert "EXECUTED TOOL: check_hash_circl" in tool_results_content
    assert "FOUND: fake_malware.exe" in tool_results_content


async def test_supporter_node_finish_analysis_interception(
    mocker, base_state, graph_config
):
    # Arrange
    base_state["history"] = [{"role": "analyst", "content": "Analysis finished."}]

    # Simulate the LLM invoking the virtual finish_analysis tool
    ai_tool_call = AIMessage(
        content="",
        tool_calls=[
            {"id": "call_fake123", "name": "finish_analysis", "args": {"is_safe": True}}
        ],
    )
    mock_llm_factory(mocker, "app.analysis_ai.graph.nodes.supporter", ai_tool_call)

    # Act
    result = await supporter_node(base_state, graph_config)

    # Assert
    # Verify the workflow exit conditions are properly set
    assert result["is_finished"] is True
    assert result["is_system_safe"] is True
    assert "history" in result  # Should append the final result log


async def test_formatter_node_success(mocker, base_state, graph_config):
    # Arrange
    base_state["history"] = [
        {"role": "analyst", "content": "Found 1 threat."},
        {"role": "tool_results", "content": "Threat mitigated."},
    ]

    expected_markdown = "# Final Forensic Report\nThreat mitigated."
    mock_llm_factory(
        mocker,
        "app.analysis_ai.graph.nodes.formatter",
        AIMessage(content=expected_markdown),
    )

    # Act
    result = await formatter_node(base_state, graph_config)

    # Assert
    # Formatter is the terminal node; it sets the final_report key
    assert result["final_report"] == expected_markdown
