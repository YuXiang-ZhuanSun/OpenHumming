from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    actions: list[str]
    memory_updates: dict[str, bool]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    result = request.app.state.runtime.respond(payload.session_id, payload.message)
    return ChatResponse(
        session_id=result.session_id,
        response=result.response,
        actions=result.actions,
        memory_updates=result.memory_updates,
    )


@router.get("/memory/agent")
def get_agent_memory(request: Request) -> dict[str, str]:
    path = request.app.state.paths.agent_profile
    return {"content": path.read_text(encoding="utf-8")}


@router.get("/memory/user")
def get_user_memory(request: Request) -> dict[str, str]:
    path = request.app.state.paths.user_profile
    return {"content": path.read_text(encoding="utf-8")}
