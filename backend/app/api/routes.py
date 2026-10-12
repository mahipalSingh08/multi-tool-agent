from fastapi import APIRouter, HTTPException, status
from app.agent.orchestrator import run_agent
from app.config import get_settings
from app.models import AgentRequest, AgentResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        providers={
            "openai_configured": settings.is_openai_configured,
            "web_search_configured": settings.is_web_search_configured,
            "weather_configured": settings.is_weather_configured,
        },
    )


@router.post("/agent", response_model=AgentResponse)
async def handle_agent_query(request: AgentRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Query cannot be empty or only whitespace.",
        )

    response = await run_agent(query)
    return response
