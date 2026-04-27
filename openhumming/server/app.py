from fastapi import FastAPI

from openhumming.agent.runtime import AgentRuntime
from openhumming.config import Settings, configure_logging, get_settings
from openhumming.llm import build_provider
from openhumming.memory.store import MemoryStore
from openhumming.scheduler.manager import TaskManager
from openhumming.server.routes_chat import router as chat_router
from openhumming.server.routes_skills import router as skills_router
from openhumming.server.routes_tasks import router as tasks_router
from openhumming.server.websocket import router as websocket_router
from openhumming.skills.manager import SkillManager
from openhumming.tools import build_default_registry
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    paths = WorkspacePaths.from_root(resolved_settings.workspace_root)
    initialize_workspace(paths)

    memory_store = MemoryStore(paths)
    skill_manager = SkillManager(paths.skills_dir)
    task_manager = TaskManager(paths.tasks_file)
    tool_registry = build_default_registry(paths, skill_manager, task_manager)
    runtime = AgentRuntime(
        settings=resolved_settings,
        memory_store=memory_store,
        provider=build_provider(resolved_settings),
        trace_recorder=TraceRecorder(paths),
        skill_manager=skill_manager,
        tool_registry=tool_registry,
    )

    app = FastAPI(
        title=resolved_settings.app_name,
        summary=resolved_settings.app_tagline,
        version="0.1.0",
    )
    app.state.settings = resolved_settings
    app.state.paths = paths
    app.state.memory_store = memory_store
    app.state.skill_manager = skill_manager
    app.state.task_manager = task_manager
    app.state.runtime = runtime

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": resolved_settings.app_name,
            "tagline": resolved_settings.app_tagline,
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(chat_router)
    app.include_router(skills_router)
    app.include_router(tasks_router)
    app.include_router(websocket_router)
    return app
