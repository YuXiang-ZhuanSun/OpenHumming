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
    result = runtime.respond("session-loop", "Remember that I prefer Python")

    assert result.session_id == "session-loop"
    assert "Remember that I prefer Python" in result.response
    assert result.memory_updates["user"] is True
    assert result.applied_memory_updates
    assert workspace_paths.trace_file().exists()

    trace_lines = workspace_paths.trace_file().read_text(encoding="utf-8").splitlines()
    assert len(trace_lines) >= 3


def test_agent_runtime_executes_file_read_tool(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)
    result = runtime.respond("session-tools", "Please read `agent.md`")

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
        "Please read `agent.md`, list the `skills` directory, then turn this workflow into skill: Agent Profile Reader",
    )

    created_skill = workspace_paths.skill_drafts_dir / "agent_profile_reader.md"
    assert "tool:file_read" in result.actions
    assert "tool:list_dir" in result.actions
    assert "create_skill_draft" in result.actions
    assert result.created_skill_draft is not None
    assert result.created_skill_draft["slug"] == "agent_profile_reader"
    assert created_skill.exists()
    assert "Created skill draft: Agent Profile Reader" in result.response


def test_agent_runtime_applies_structured_memory_updates(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)

    result = runtime.respond(
        "session-memory",
        "Please read `agent.md` and remember that I prefer concise implementation-ready updates.",
    )

    user_profile = workspace_paths.user_profile.read_text(encoding="utf-8")
    agent_profile = workspace_paths.agent_profile.read_text(encoding="utf-8")

    assert "propose_memory_updates" in result.actions
    assert "update_user_memory" in result.actions
    assert "update_agent_memory" in result.actions
    assert result.memory_updates == {"agent": True, "user": True}
    assert any(proposal.section == "## Interaction Style" for proposal in result.memory_proposals)
    assert any(update.section == "## Working Style" for update in result.applied_memory_updates)
    assert "Prefers concise implementation-ready updates" in user_profile
    assert "Match the user's preferred collaboration style: concise implementation-ready updates" in agent_profile


def test_agent_runtime_normalizes_current_project_name(settings, workspace_paths) -> None:
    runtime = build_runtime(settings, workspace_paths)

    result = runtime.respond(
        "session-project",
        "I'm working on a local-first autonomous agent runtime.",
    )

    user_profile = workspace_paths.user_profile.read_text(encoding="utf-8")

    assert result.memory_updates["user"] is True
    assert "Local-first autonomous agent runtime" in user_profile


def test_agent_runtime_updates_existing_skill_draft_reuse_metadata(
    settings,
    workspace_paths,
) -> None:
    runtime = build_runtime(settings, workspace_paths)
    message = (
        "Please read `agent.md`, list the `skills` directory, then turn this workflow into skill: "
        "Agent Profile Reader"
    )

    first = runtime.respond("session-duplicate-1", message)
    second = runtime.respond("session-duplicate-2", message)

    draft_files = list(workspace_paths.skill_drafts_dir.glob("agent_profile_reader.md"))

    assert first.created_skill_draft is not None
    assert second.created_skill_draft is not None
    assert "update_skill_draft" in second.actions
    assert second.created_skill_draft["event"] == "updated"
    assert second.created_skill_draft["metadata"]["times_reused"] == 1
    assert second.created_skill_draft["metadata"]["created_from_sessions"] == [
        "session-duplicate-1",
        "session-duplicate-2",
    ]
    assert len(draft_files) == 1


def test_agent_runtime_replaces_interaction_style_with_newer_preference(
    settings,
    workspace_paths,
) -> None:
    runtime = build_runtime(settings, workspace_paths)

    runtime.respond(
        "session-style-1",
        "Remember that I prefer terse engineering updates.",
    )
    runtime.respond(
        "session-style-2",
        "From now on, please give me detailed step-by-step explanations.",
    )

    user_profile = workspace_paths.user_profile.read_text(encoding="utf-8")
    agent_profile = workspace_paths.agent_profile.read_text(encoding="utf-8")

    assert "Prefers detailed step-by-step explanations" in user_profile
    assert "Prefers terse engineering updates" not in user_profile
    assert "Match the user's preferred collaboration style: detailed step-by-step explanations" in agent_profile
