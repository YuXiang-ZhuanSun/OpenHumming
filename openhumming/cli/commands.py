from datetime import date
from pathlib import Path

import typer
import uvicorn

from openhumming.agent.runtime import AgentRuntime
from openhumming.config import Settings, get_settings
from openhumming.llm import build_provider, build_provider_from_profile
from openhumming.llm.provider_settings import ProviderSettingsStore
from openhumming.memory.reviewer import DailyReviewService
from openhumming.memory.store import MemoryStore
from openhumming.scheduler.manager import TaskManager
from openhumming.server.app import create_app
from openhumming.skills.manager import SkillManager
from openhumming.tools import build_default_registry
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths

app = typer.Typer(help="OpenHumming local-first Python agent runtime.")


def _resolve_settings(
    *,
    workspace: Path | None = None,
    provider: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> Settings:
    settings = get_settings()
    updates: dict[str, object] = {}
    if workspace is not None:
        updates["workspace_root"] = workspace.resolve()
    if provider is not None:
        updates["provider"] = provider
    if host is not None:
        updates["host"] = host
    if port is not None:
        updates["port"] = port
    return settings.model_copy(update=updates)


def _build_runtime(
    settings: Settings,
    *,
    prefer_workspace_provider: bool = True,
) -> AgentRuntime:
    paths = WorkspacePaths.from_root(settings.workspace_root)
    initialize_workspace(paths)
    memory_store = MemoryStore(paths)
    skill_manager = SkillManager(paths.skills_dir)
    task_manager = TaskManager(paths.tasks_file)
    tool_registry = build_default_registry(paths, skill_manager, task_manager)
    provider = build_provider(settings)
    if prefer_workspace_provider:
        document = ProviderSettingsStore(paths.provider_settings_file, settings).load()
        try:
            provider = build_provider_from_profile(document.active_profile)
        except ValueError:
            provider = build_provider(settings)
    return AgentRuntime(
        settings=settings,
        memory_store=memory_store,
        provider=provider,
        trace_recorder=TraceRecorder(paths),
        skill_manager=skill_manager,
        tool_registry=tool_registry,
    )


def _build_daily_review_service(settings: Settings) -> DailyReviewService:
    paths = WorkspacePaths.from_root(settings.workspace_root)
    initialize_workspace(paths)
    memory_store = MemoryStore(paths)
    skill_manager = SkillManager(paths.skills_dir)
    task_manager = TaskManager(paths.tasks_file)
    return DailyReviewService(
        paths=paths,
        memory_store=memory_store,
        skill_manager=skill_manager,
        task_manager=task_manager,
        trace_recorder=TraceRecorder(paths),
    )


@app.command("init")
def init_command(
    workspace: Path = typer.Option(Path("workspace"), help="Workspace directory."),
    overwrite: bool = typer.Option(False, help="Overwrite seeded workspace files."),
) -> None:
    paths = WorkspacePaths.from_root(workspace)
    created = initialize_workspace(paths, overwrite=overwrite)
    if created:
        for item in created:
            typer.echo(item)
        return
    typer.echo("Workspace already initialized.")


@app.command("serve")
def serve_command(
    host: str | None = typer.Option(None, help="Host to bind."),
    port: int | None = typer.Option(None, help="Port to bind."),
    workspace: Path | None = typer.Option(None, help="Workspace directory."),
    provider: str | None = typer.Option(None, help="Provider name."),
) -> None:
    settings = _resolve_settings(
        workspace=workspace,
        provider=provider,
        host=host,
        port=port,
    )
    app_instance = create_app(
        settings,
        prefer_workspace_provider=provider is None,
    )
    uvicorn.run(app_instance, host=settings.host, port=settings.port)


@app.command("chat")
def chat_command(
    message: str | None = typer.Argument(None, help="Optional single-turn message."),
    session_id: str | None = typer.Option(None, help="Conversation session id."),
    workspace: Path | None = typer.Option(None, help="Workspace directory."),
    provider: str | None = typer.Option(None, help="Provider name."),
) -> None:
    settings = _resolve_settings(workspace=workspace, provider=provider)
    runtime = _build_runtime(
        settings,
        prefer_workspace_provider=provider is None,
    )

    if message is not None:
        result = runtime.respond(session_id, message)
        typer.echo(result.response)
        return

    typer.echo("Interactive chat. Type 'exit' to quit.")
    active_session = session_id
    while True:
        user_message = typer.prompt("You")
        if user_message.strip().lower() in {"exit", "quit"}:
            break
        result = runtime.respond(active_session, user_message)
        active_session = result.session_id
        typer.echo(f"OpenHumming: {result.response}")


@app.command("daily-review")
def daily_review_command(
    workspace: Path | None = typer.Option(None, help="Workspace directory."),
    review_date: str | None = typer.Option(
        None,
        help="Optional review date in YYYY-MM-DD format.",
    ),
) -> None:
    settings = _resolve_settings(workspace=workspace)
    service = _build_daily_review_service(settings)
    target_date = date.fromisoformat(review_date) if review_date else None
    result = service.run(target_date)
    typer.echo(str(result.summary_path))
    if result.user_updates:
        typer.echo("User updates:")
        for item in result.user_updates:
            typer.echo(f"- {item}")
    if result.agent_updates:
        typer.echo("Agent updates:")
        for item in result.agent_updates:
            typer.echo(f"- {item}")
