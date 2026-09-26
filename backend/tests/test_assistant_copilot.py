"""
Unit and integration tests for Farm AI Copilot.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.assistant_tools import AssistantTools
from app.services.assistant_orchestrator import AssistantOrchestrator

client = TestClient(app)


def test_assistant_tools_get_farm_summary():
    res = AssistantTools.get_farm_summary(user_id="test_farmer_user")
    assert "status" in res
    assert "farms" in res
    assert "active_crops" in res


def test_assistant_tools_weather_and_market():
    import asyncio
    from app.services.weather_service import WeatherService
    ws = WeatherService()
    w = asyncio.run(ws.get_current_weather(22.5726, 88.3639))
    assert w is not None
    assert "temperature_c" in w or "temperature" in w or "current" in w

    m = AssistantTools.get_market_current("Rice")
    assert m.get("status") == "success"



def test_assistant_orchestrator_process_chat():
    res = AssistantOrchestrator.process_chat(
        user_id="test_copilot_user",
        message="What should I do today?",
    )
    assert "conversation_id" in res
    assert "content" in res
    assert res.get("role") == "assistant"
    assert len(res.get("actions", [])) > 0


def test_assistant_api_chat_endpoint():
    response = client.post(
        "/api/v1/assistant/chat",
        headers={"X-User-ID": "test_user_copilot"},
        json={
            "message": "Should I irrigate my rice field today?",
            "page_context": {"route": "/irrigation", "page_name": "Irrigation Intelligence"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "content" in data


def test_assistant_api_conversations_list():
    response = client.get(
        "/api/v1/assistant/conversations",
        headers={"X-User-ID": "test_user_copilot"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
