from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["skills"])


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str
    when_to_use: str
    inputs: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(default_factory=list)
    output: str


class SkillResponse(BaseModel):
    name: str
    slug: str
    description: str
    content: str
    path: str
    status: str
    metadata: dict[str, object]


@router.get("/skills", response_model=list[SkillResponse])
def list_skills(request: Request) -> list[SkillResponse]:
    skills = request.app.state.skill_manager.list_skills()
    return [
        SkillResponse(
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            content=skill.content,
            path=str(skill.path),
            status=skill.status,
            metadata=skill.metadata,
        )
        for skill in skills
    ]


@router.get("/skills/drafts", response_model=list[SkillResponse])
def list_skill_drafts(request: Request) -> list[SkillResponse]:
    skills = request.app.state.skill_manager.list_skill_drafts()
    return [
        SkillResponse(
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            content=skill.content,
            path=str(skill.path),
            status=skill.status,
            metadata=skill.metadata,
        )
        for skill in skills
    ]


@router.post("/skills", response_model=SkillResponse)
def create_skill(payload: SkillCreateRequest, request: Request) -> SkillResponse:
    skill = request.app.state.skill_manager.create_skill(
        name=payload.name,
        description=payload.description,
        when_to_use=payload.when_to_use,
        inputs=payload.inputs,
        procedure=payload.procedure,
        output=payload.output,
    )
    return SkillResponse(
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        content=skill.content,
        path=str(skill.path),
        status=skill.status,
        metadata=skill.metadata,
    )
