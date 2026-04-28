from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from openhumming import __version__
from openhumming.agent.runtime import AgentRuntime
from openhumming.config import Settings, configure_logging, get_settings
from openhumming.llm import build_provider, build_provider_from_profile
from openhumming.llm.provider_settings import ProviderSettingsStore
from openhumming.memory.reviewer import DailyReviewService
from openhumming.memory.store import MemoryStore
from openhumming.scheduler.manager import TaskManager
from openhumming.scheduler.runner import TaskRunner
from openhumming.server.routes_chat import router as chat_router
from openhumming.server.routes_reviews import router as reviews_router
from openhumming.server.routes_settings import router as settings_router
from openhumming.server.routes_skills import router as skills_router
from openhumming.server.routes_tasks import router as tasks_router
from openhumming.server.routes_ui import STATIC_DIR, router as ui_router
from openhumming.server.websocket import router as websocket_router
from openhumming.skills.manager import SkillManager
from openhumming.tools import build_default_registry
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths


def create_app(
    settings: Settings | None = None,
    *,
    prefer_workspace_provider: bool = True,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    paths = WorkspacePaths.from_root(resolved_settings.workspace_root)
    initialize_workspace(paths)

    memory_store = MemoryStore(paths)
    skill_manager = SkillManager(paths.skills_dir)
    task_manager = TaskManager(paths.tasks_file)
    tool_registry = build_default_registry(paths, skill_manager, task_manager)
    provider_settings_store = ProviderSettingsStore(paths.provider_settings_file, resolved_settings)
    provider = build_provider(resolved_settings)
    if prefer_workspace_provider:
        provider_settings_document = provider_settings_store.load()
        try:
            provider = build_provider_from_profile(provider_settings_document.active_profile)
        except ValueError:
            provider = build_provider(resolved_settings)
    runtime = AgentRuntime(
        settings=resolved_settings,
        memory_store=memory_store,
        provider=provider,
        trace_recorder=TraceRecorder(paths),
        skill_manager=skill_manager,
        tool_registry=tool_registry,
    )
    trace_recorder = runtime.trace_recorder
    daily_review_service = DailyReviewService(
        paths=paths,
        memory_store=memory_store,
        skill_manager=skill_manager,
        task_manager=task_manager,
        trace_recorder=trace_recorder,
    )
    task_runner = TaskRunner(
        task_manager=task_manager,
        runtime=runtime,
        paths=paths,
        trace_recorder=trace_recorder,
        timezone_name=resolved_settings.scheduler_timezone,
        sync_interval_seconds=resolved_settings.scheduler_sync_interval_seconds,
        daily_review_service=daily_review_service,
        daily_review_enabled=resolved_settings.daily_review_enabled,
        daily_review_hour=resolved_settings.daily_review_hour,
        daily_review_minute=resolved_settings.daily_review_minute,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.task_runner = task_runner
        if resolved_settings.scheduler_enabled:
            task_runner.start()
        try:
            yield
        finally:
            task_runner.shutdown()

    app = FastAPI(
        title=resolved_settings.app_name,
        summary=resolved_settings.app_tagline,
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.paths = paths
    app.state.memory_store = memory_store
    app.state.skill_manager = skill_manager
    app.state.task_manager = task_manager
    app.state.task_runner = task_runner
    app.state.provider_settings_store = provider_settings_store
    app.state.daily_review_service = daily_review_service
    app.state.runtime = runtime
    app.state.trace_recorder = trace_recorder

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": resolved_settings.app_name,
            "tagline": resolved_settings.app_tagline,
            "ui_url": "/ui",
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(chat_router)
    app.include_router(reviews_router)
    app.include_router(settings_router)
    app.include_router(skills_router)
    app.include_router(tasks_router)
    app.include_router(ui_router)
    app.include_router(websocket_router)
    app.mount("/ui/static", StaticFiles(directory=STATIC_DIR), name="ui-static")
    return app
