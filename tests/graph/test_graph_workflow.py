import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage

from app.analysis_ai.graph.graph import route_from_supporter, workflow_app
from app.analysis_ai.graph.graph_config import GraphConfig
from app.analysis_ai.graph.state import AgentState


@pytest.fixture
def graph_config(mock_notifier):
    """Provides a valid LangGraph configuration context."""
    return GraphConfig.set_notifier(mock_notifier)


# ==========================================
# 1. UNIT TESTING THE ROUTER LOGIC
# ==========================================


def test_router_forces_formatter_on_iteration_limit():
    # Arrange
    state = AgentState(iteration_count=10, is_finished=False)

    # Act
    next_node = route_from_supporter(state)

    # Assert
    assert next_node == "formatter", "Should break infinite loops at limit 10."


def test_router_routes_to_formatter_when_finished():
    # Arrange
    state = AgentState(iteration_count=2, is_finished=True)

    # Act
    next_node = route_from_supporter(state)

    # Assert
    assert next_node == "formatter", "Should route to formatter if explicit finish."


def test_router_loops_back_to_analyst_normally():
    # Arrange
    state = AgentState(iteration_count=2, is_finished=False)

    # Act
    next_node = route_from_supporter(state)

    # Assert
    assert next_node == "analyst", "Should loop back for continuous analysis."


# ==========================================
# 2. INTEGRATION TESTING THE FULL WORKFLOW
# ==========================================


async def test_full_workflow_execution(mocker, graph_config):
    """
    Executes the entire compiled state graph from START to END.
    We mock the LLM responses to force a specific path:
    Analyst (asks to finish) -> Supporter (calls finish tool) -> Formatter (generates report).
    """
    # Arrange: Initial clean state
    initial_state = {
        "system_data": "Mocked OS Data",
        "history": [],
        "iteration_count": 0,
        "is_finished": False,
        "tool_requests": [],
        "final_report": "",
        "is_system_safe": False,
    }

    # 1. Mock Analyst LLM: Pretend it reviewed and decided to finish
    mock_analyst_llm = MagicMock()
    mock_analyst_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Analysis finished.")
    )

    # 2. Mock Supporter LLM: Pretend it translates the intent into the finish tool
    mock_supporter_llm = MagicMock()
    mock_supporter_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_finish123",
                    "name": "finish_analysis",
                    "args": {"is_safe": True},
                }
            ],
        )
    )
    mock_supporter_llm.bind_tools.return_value = mock_supporter_llm

    # 3. Mock Formatter LLM: Pretend it generates the final Markdown
    mock_formatter_llm = MagicMock()
    mock_formatter_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="# Final Report")
    )

    # Apply the patches to the factory function inside each node's module
    mocker.patch(
        "app.analysis_ai.graph.nodes.analyst.get_gemini_llm",
        return_value=mock_analyst_llm,
    )
    mocker.patch(
        "app.analysis_ai.graph.nodes.supporter.get_gemini_llm",
        return_value=mock_supporter_llm,
    )
    mocker.patch(
        "app.analysis_ai.graph.nodes.formatter.get_gemini_llm",
        return_value=mock_formatter_llm,
    )

    # Act: Trigger the compiled LangGraph workflow
    final_state = await workflow_app.ainvoke(initial_state, config=graph_config)

    # Assert: Verify the state traversed correctly through the graph
    assert final_state["iteration_count"] == 1
    assert final_state["is_finished"] is True
    assert final_state["is_system_safe"] is True
    assert final_state["final_report"] == "# Final Report"

    # Verify the history accumulator collected messages from Analyst and Tool
    assert len(final_state["history"]) == 2
    assert final_state["history"][0]["role"] == "analyst"
    assert final_state["history"][1]["role"] == "tool_results"
    assert "Analysis marked as complete" in final_state["history"][1]["content"]


async def test_full_workflow_reaches_iteration_limit(mocker, graph_config):
    """
    Tests the emergency brake: If the LLMs get stuck in a loop without ever
    calling 'finish_analysis', the router MUST force the formatter at iteration 10.
    """
    # Arrange: We start near the edge of the cliff (iteration 9)
    initial_state = {
        "system_data": "Mocked OS Data",
        "history": [],
        "iteration_count": 9,
        "is_finished": False,
        "tool_requests": [],
        "final_report": "",
        "is_system_safe": False,
    }

    # 1. Analyst keeps thinking and never asks to finish
    mock_analyst_llm = MagicMock()
    mock_analyst_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Still analyzing...")
    )

    # 2. Supporter finds no tool calls in the Analyst's message
    mock_supporter_llm = MagicMock()
    mock_supporter_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="No tools executed.", tool_calls=[])
    )
    mock_supporter_llm.bind_tools.return_value = mock_supporter_llm

    # 3. Formatter should eventually be called
    mock_formatter_llm = MagicMock()
    mock_formatter_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="# Forced Final Report")
    )

    mocker.patch(
        "app.analysis_ai.graph.nodes.analyst.get_gemini_llm",
        return_value=mock_analyst_llm,
    )
    mocker.patch(
        "app.analysis_ai.graph.nodes.supporter.get_gemini_llm",
        return_value=mock_supporter_llm,
    )
    mocker.patch(
        "app.analysis_ai.graph.nodes.formatter.get_gemini_llm",
        return_value=mock_formatter_llm,
    )

    # Act
    # Analyst (iter 9) -> Supporter -> (router sees iter 10) -> Formatter -> END
    final_state = await workflow_app.ainvoke(initial_state, config=graph_config)

    # Assert
    assert final_state["iteration_count"] == 10
    assert final_state["is_finished"] is False  # Explicit finish was never called
    assert final_state["final_report"] == "# Forced Final Report"

    # Verify the history accumulator reflects the aborted state
    assert len(final_state["history"]) == 2
    assert final_state["history"][0]["role"] == "analyst"


async def test_supporter_recovers_from_tool_failure(mocker, graph_config):
    """
    Ensures that if an external tool crashes (e.g., an API goes down),
    the workflow does not explode. The Supporter must catch the error, log it,
    and return it to the Analyst for re-evaluation in the next cycle.
    """
    from app.analysis_ai.graph.nodes import supporter

    # Arrange: Start fresh
    initial_state = {
        "system_data": "Mocked OS Data",
        "history": [],
        "iteration_count": 0,
        "is_finished": False,
        "tool_requests": [],
        "final_report": "",
        "is_system_safe": False,
    }

    # 1. Analyst wants to check a hash
    mock_analyst_llm = MagicMock()
    mock_analyst_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Check this hash.")
    )
    mocker.patch(
        "app.analysis_ai.graph.nodes.analyst.get_gemini_llm",
        return_value=mock_analyst_llm,
    )

    # 2. Supporter attempts to call the tool
    mock_supporter_llm = MagicMock()
    mock_supporter_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_crash123",
                    "name": "check_hash_circl",
                    "args": {"hashes": ["bad_hash"]},
                }
            ],
        )
    )
    mock_supporter_llm.bind_tools.return_value = mock_supporter_llm
    mocker.patch(
        "app.analysis_ai.graph.nodes.supporter.get_gemini_llm",
        return_value=mock_supporter_llm,
    )

    # 3. MOCK A CRITICAL TOOL FAILURE
    mock_crashing_tool = AsyncMock()
    mock_crashing_tool.ainvoke.side_effect = Exception("API Server down 500")
    mocker.patch.dict(supporter.TOOLS_DICT, {"check_hash_circl": mock_crashing_tool})

    # Act
    # Because we are testing the recovery mid-workflow, we only invoke the nodes up to Supporter.
    # We do not run the full graph because the next node would loop back to Analyst infinitely in this mock setup.
    from app.analysis_ai.graph.nodes.analyst import analyst_node
    from app.analysis_ai.graph.nodes.supporter import supporter_node

    # Run Analyst manually
    state_after_analyst = await analyst_node(initial_state, graph_config)
    initial_state.update(state_after_analyst)

    # Run Supporter manually and observe the crash handling
    state_after_supporter = await supporter_node(initial_state, graph_config)

    # Assert
    assert state_after_supporter["is_finished"] is False
    assert "history" in state_after_supporter

    tool_results = state_after_supporter["history"][0]["content"]
    assert "CRITICAL TOOL ERROR" in tool_results
    assert "API Server down 500" in tool_results
