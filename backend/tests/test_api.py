import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models import AgentResponse


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "providers" in data
    assert "openai_configured" in data["providers"]
    assert "web_search_configured" in data["providers"]
    assert "weather_configured" in data["providers"]


@pytest.mark.asyncio
async def test_agent_empty_query_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/agent", json={"query": "   "})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agent_endpoint_success(monkeypatch):
    async def mock_run_agent(query: str):
        return AgentResponse(
            query=query,
            answer="Calculated answer is 42.",
            tools_used=[],
            sources=[],
            success=True,
        )

    monkeypatch.setattr("app.api.routes.run_agent", mock_run_agent)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/agent", json={"query": "What is the meaning of life?"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["answer"] == "Calculated answer is 42."
    assert data["query"] == "What is the meaning of life?"
