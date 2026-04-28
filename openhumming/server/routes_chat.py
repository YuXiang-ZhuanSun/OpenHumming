from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["chat"])


class MemoryProposalResponse(BaseModel):
    target: str
    section: str
    content: str
    reason: str
    confidence: float
    operation: str = "add"
    anchor: str | None = None
    category: str | None = None


class AppliedMemoryUpdateResponse(BaseModel):
    target: str
    section: str
    content: str
    path: str
    operation: str = "add"
    replaced: str | None = None


class SkillDraftResponse(BaseModel):
    name: str
    slug: str
    description: str
    path: str
    status: str
    metadata: dict[str, object]
    event: str = "created"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    actions: list[str]
    memory_updates: dict[str, bool]
    memory_proposals: list[MemoryProposalResponse]
    applied_memory_updates: list[AppliedMemoryUpdateResponse]
    created_skill_draft: SkillDraftResponse | None = None


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    result = request.app.state.runtime.respond(payload.session_id, payload.message)
    return ChatResponse(
        session_id=result.session_id,
        response=result.response,
        actions=result.actions,
        memory_updates=result.memory_updates,
        memory_proposals=[
            MemoryProposalResponse(
                target=proposal.target,
                section=proposal.section,
                content=proposal.content,
                reason=proposal.reason,
                confidence=proposal.confidence,
                operation=proposal.operation,
                anchor=proposal.anchor,
                category=proposal.category,
            )
            for proposal in result.memory_proposals
        ],
        applied_memory_updates=[
            AppliedMemoryUpdateResponse(
                target=update.target,
                section=update.section,
                content=update.content,
                path=str(update.path),
                operation=update.operation,
                replaced=update.replaced,
            )
            for update in result.applied_memory_updates
        ],
        created_skill_draft=(
            SkillDraftResponse(**result.created_skill_draft)
            if result.created_skill_draft is not None
            else None
        ),
    )


@router.get("/memory/agent")
def get_agent_memory(request: Request) -> dict[str, str]:
    path = request.app.state.paths.agent_profile
    return {"content": path.read_text(encoding="utf-8")}


@router.get("/memory/user")
def get_user_memory(request: Request) -> dict[str, str]:
    path = request.app.state.paths.user_profile
    return {"content": path.read_text(encoding="utf-8")}
