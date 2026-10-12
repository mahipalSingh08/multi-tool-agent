import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.agent.orchestrator import run_agent
from app.config import get_settings


@pytest.mark.asyncio
async def test_orchestrator_missing_api_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", "")
    res = await run_agent("Hello")
    assert res.success is False
    assert "OpenAI API key" in res.error


@pytest.mark.asyncio
async def test_orchestrator_direct_answer(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", "sk-mock-key")

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "An AI agent is an autonomous software entity."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    monkeypatch.setattr("app.agent.orchestrator.AsyncOpenAI", lambda api_key: mock_client)

    res = await run_agent("Explain what an AI agent is")
    assert res.success is True
    assert "AI agent is an autonomous" in res.answer
    assert len(res.tools_used) == 0


@pytest.mark.asyncio
async def test_orchestrator_single_tool_execution(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", "sk-mock-key")

    # Round 1: Model requests calculator tool
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_calc_1"
    mock_tool_call.function.name = "calculator"
    mock_tool_call.function.arguments = json.dumps({"expression": "15% of 2400"})

    mock_message_1 = MagicMock()
    mock_message_1.tool_calls = [mock_tool_call]
    mock_message_1.model_dump = MagicMock(return_value={
        "role": "assistant",
        "tool_calls": [{"id": "call_calc_1", "type": "function", "function": {"name": "calculator", "arguments": '{"expression":"15% of 2400"}'}}],
    })

    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=mock_message_1)]

    # Round 2: Model receives result and provides final text
    mock_message_2 = MagicMock()
    mock_message_2.tool_calls = None
    mock_message_2.content = "15% of 2400 is 360."

    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=mock_message_2)]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response_1, mock_response_2])

    monkeypatch.setattr("app.agent.orchestrator.AsyncOpenAI", lambda api_key: mock_client)

    res = await run_agent("What is 15% of 2400?")
    assert res.success is True
    assert "360" in res.answer
    assert len(res.tools_used) == 1
    assert res.tools_used[0].name == "calculator"
    assert res.tools_used[0].status == "success"


@pytest.mark.asyncio
async def test_orchestrator_multiple_tools(monkeypatch):
    monkeypatch.setattr(get_settings(), "openai_api_key", "sk-mock-key")
    monkeypatch.setattr(get_settings(), "weather_api_key", "mock-weather-key")

    # Round 1: Model requests two weather calls (Delhi and Jaipur)
    mock_tool_delhi = MagicMock()
    mock_tool_delhi.id = "call_delhi"
    mock_tool_delhi.function.name = "get_weather"
    mock_tool_delhi.function.arguments = json.dumps({"location": "Delhi"})

    mock_tool_jaipur = MagicMock()
    mock_tool_jaipur.id = "call_jaipur"
    mock_tool_jaipur.function.name = "get_weather"
    mock_tool_jaipur.function.arguments = json.dumps({"location": "Jaipur"})

    mock_message_1 = MagicMock()
    mock_message_1.tool_calls = [mock_tool_delhi, mock_tool_jaipur]
    mock_message_1.model_dump = MagicMock(return_value={
        "role": "assistant",
        "tool_calls": [
            {"id": "call_delhi", "type": "function", "function": {"name": "get_weather", "arguments": '{"location":"Delhi"}'}},
            {"id": "call_jaipur", "type": "function", "function": {"name": "get_weather", "arguments": '{"location":"Jaipur"}'}},
        ],
    })

    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=mock_message_1)]

    # Mock weather tool response
    async def mock_weather(loc, units="metric"):
        return {
            "success": True,
            "location": loc,
            "data": {"temperature": "30°C", "description": "Sunny"},
        }
    monkeypatch.setattr("app.agent.orchestrator.get_weather", mock_weather)

    # Round 2: Final comparison answer
    mock_message_2 = MagicMock()
    mock_message_2.tool_calls = None
    mock_message_2.content = "Delhi and Jaipur both have temperatures around 30°C."

    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock(message=mock_message_2)]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response_1, mock_response_2])
    monkeypatch.setattr("app.agent.orchestrator.AsyncOpenAI", lambda api_key: mock_client)

    res = await run_agent("Is the weather in Delhi warmer than in Jaipur?")
    assert res.success is True
    assert len(res.tools_used) == 2
    assert all(t.status == "success" for t in res.tools_used)
