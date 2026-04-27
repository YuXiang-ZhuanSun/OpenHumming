from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["tasks"])


class TaskCreateRequest(BaseModel):
    natural_language: str = Field(min_length=1)
    prompt: str | None = None
    title: str | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    prompt: str
    schedule: str
    enabled: bool
    created_at: str
    natural_language: str


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(request: Request) -> list[TaskResponse]:
    tasks = request.app.state.task_manager.list_tasks()
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            prompt=task.prompt,
            schedule=task.schedule,
            enabled=task.enabled,
            created_at=task.created_at,
            natural_language=task.natural_language,
        )
        for task in tasks
    ]


@router.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, request: Request) -> TaskResponse:
    task = request.app.state.task_manager.create_from_text(
        natural_language=payload.natural_language,
        prompt=payload.prompt,
        title=payload.title,
    )
    task_runner = getattr(request.app.state, "task_runner", None)
    if task_runner is not None:
        task_runner.sync_jobs()
    return TaskResponse(
        id=task.id,
        title=task.title,
        prompt=task.prompt,
        schedule=task.schedule,
        enabled=task.enabled,
        created_at=task.created_at,
        natural_language=task.natural_language,
    )
