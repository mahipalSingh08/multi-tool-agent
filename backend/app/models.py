from typing import Literal, Optional
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User natural language query")


class ToolExecution(BaseModel):
    name: str
    status: Literal["success", "error", "skipped"]
    summary: str
    detail: Optional[str] = None


class SourceItem(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class AgentResponse(BaseModel):
    query: str
    answer: str
    tools_used: list[ToolExecution] = Field(default_factory=list)
    sources: list[SourceItem] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    providers: dict[str, bool]
