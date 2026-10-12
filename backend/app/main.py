from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Multi-Tool AI Agent API",
    description="Backend API orchestration for OpenAI tool calling (Web Search, Calculator, Weather)",
    version="1.0.0",
)

allowed_origins = [
    settings.frontend_origin,
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Multi-Tool AI Agent API",
        "docs": "/docs",
        "health": "/api/health",
    }
