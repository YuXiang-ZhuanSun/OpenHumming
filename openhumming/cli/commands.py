from pathlib import Path

import typer
import uvicorn

from openhumming.agent.runtime import AgentRuntime
from openhumming.config import Settings, get_settings
from openhumming.llm import build_provider
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


def _build_runtime(settings: Settings) -> AgentRuntime:
    paths = WorkspacePaths.from_root(settings.workspace_root)
    initialize_workspace(paths)
    memory_store = MemoryStore(paths)
    skill_manager = SkillManager(paths.skills_dir)
    task_manager = TaskManager(paths.tasks_file)
    tool_registry = build_default_registry(paths, skill_manager, task_manager)
    return AgentRuntime(
        settings=settings,
        memory_store=memory_store,
        provider=build_provider(settings),
        trace_recorder=TraceRecorder(paths),
        skill_manager=skill_manager,
        tool_registry=tool_registry,
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
    app_instance = create_app(settings)
    uvicorn.run(app_instance, host=settings.host, port=settings.port)


@app.command("chat")
def chat_command(
    message: str | None = typer.Argument(None, help="Optional single-turn message."),
    session_id: str | None = typer.Option(None, help="Conversation session id."),
    workspace: Path | None = typer.Option(None, help="Workspace directory."),
    provider: str | None = typer.Option(None, help="Provider name."),
) -> None:
    settings = _resolve_settings(workspace=workspace, provider=provider)
    runtime = _build_runtime(settings)

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
