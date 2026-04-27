from openhumming.agent.runtime import AgentRuntime
from openhumming.llm import build_provider
from openhumming.memory.store import MemoryStore
from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.tools import build_default_registry
from openhumming.trace.recorder import TraceRecorder


def build_runtime(settings, workspace_paths) -> AgentRuntime:
    skill_manager = SkillManager(workspace_paths.skills_dir)
    task_manager = TaskManager(workspace_paths.tasks_file)
    return AgentRuntime(
        settings=settings,
        memory_store=MemoryStore(workspace_paths),
        provider=build_provider(settings),
        trace_recorder=TraceRecorder(workspace_paths),
        skill_manager=skill_manager,
        tool_registry=build_default_registry(workspace_paths, skill_manager, task_manager),
    )


def test_agent_runtime_records_turn_and_trace(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)
    result = runtime.respond("session-loop", "请记住我偏好 Python")

    assert result.session_id == "session-loop"
    assert "请记住我偏好 Python" in result.response
    assert result.memory_updates["user"] is True
    assert workspace_paths.trace_file().exists()

    trace_lines = workspace_paths.trace_file().read_text(encoding="utf-8").splitlines()
    assert len(trace_lines) == 2


def test_agent_runtime_executes_file_read_tool(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)
    result = runtime.respond("session-tools", "请读取 `agent.md`")

    assert "tool:file_read" in result.actions
    assert "Tool results:" in result.response
    assert "Agent Profile" in result.response


def test_agent_runtime_injects_relevant_skill_context(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)
    result = runtime.respond(
        "session-skills",
        "I need a mature project plan for a Python agent runtime",
    )

    assert "load_skills" in result.actions
    assert "Relevant skill context:" in result.response
    assert "Create Agent Project Plan" in result.response


def test_agent_runtime_creates_skill_from_completed_workflow(
    settings,
    workspace_paths,
) -> None:
    runtime = build_runtime(settings, workspace_paths)
    result = runtime.respond(
        "session-create-skill",
        "请读取 `agent.md`，然后把这个流程沉淀成 skill: Agent Profile Reader",
    )

    created_skill = workspace_paths.skills_dir / "agent_profile_reader.md"
    assert "tool:file_read" in result.actions
    assert "create_skill" in result.actions
    assert created_skill.exists()
    assert "Created skill: Agent Profile Reader" in result.response
