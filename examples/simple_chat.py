from pathlib import Path

from openhumming.agent.runtime import AgentRuntime
from openhumming.config.settings import Settings
from openhumming.llm import build_provider
from openhumming.memory.store import MemoryStore
from openhumming.skills.manager import SkillManager
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths


def main() -> None:
    settings = Settings(workspace_root=Path("workspace"), provider="local")
    paths = WorkspacePaths.from_root(settings.workspace_root)
    initialize_workspace(paths)

    runtime = AgentRuntime(
        settings=settings,
        memory_store=MemoryStore(paths),
        provider=build_provider(settings),
        trace_recorder=TraceRecorder(paths),
        skill_manager=SkillManager(paths.skills_dir),
    )

    result = runtime.respond("demo-session", "帮我总结一下 OpenHumming 的方向。")
    print(result.response)


if __name__ == "__main__":
    main()
