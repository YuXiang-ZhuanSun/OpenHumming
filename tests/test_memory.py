from datetime import date

from openhumming.memory.reviewer import DailyReviewService
from openhumming.memory.store import MemoryStore
from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.trace.recorder import TraceRecorder


def test_memory_store_loads_profiles_and_turns(workspace_paths) -> None:
    store = MemoryStore(workspace_paths)
    initial_context = store.load_context()

    assert "OpenHumming" in initial_context.agent_profile
    assert "Python" in initial_context.user_profile
    assert initial_context.conversation_history == []

    store.save_turn("session-a", "hello", "world", metadata={"intent": "chat"})
    updated_context = store.load_context(session_id="session-a")

    assert [item.role for item in updated_context.conversation_history] == [
        "user",
        "assistant",
    ]
    assert updated_context.conversation_history[0].content == "hello"
    assert updated_context.conversation_history[1].content == "world"


def test_daily_review_writes_summary_updates_memory_and_promotes_drafts(
    workspace_paths,
) -> None:
    store = MemoryStore(workspace_paths)
    store.save_turn(
        "session-review",
        "Remember that I prefer Python tooling",
        "I will remember that preference.",
        metadata={"intent": "chat"},
    )
    skill_manager = SkillManager(workspace_paths.skills_dir)
    promoted_candidate = skill_manager.create_skill_draft(
        name="Daily Agent Profile Reader",
        description="Reusable workflow for inspecting agent profile and listing nearby files.",
        when_to_use="Use this when the user wants to inspect the agent profile workflow.",
        inputs=["target path", "workspace context"],
        procedure=["Read agent.md.", "List the skills directory.", "Summarize the result."],
        output="A reusable workspace inspection workflow.",
        metadata={
            "source": "workflow_capture",
            "confidence": 0.92,
            "created_from_sessions": ["session-review"],
            "times_reused": 0,
            "capture_reason": "The user explicitly asked to retain the finished workflow as a skill.",
        },
    )
    pending_candidate = skill_manager.create_skill_draft(
        name="Tentative Directory Notes",
        description="Low-confidence draft that should remain pending.",
        when_to_use="Use this when the workflow still needs more validation.",
        inputs=["target path"],
        procedure=["List the directory.", "Write a quick note."],
        output="A tentative draft workflow.",
        metadata={
            "source": "workflow_capture",
            "confidence": 0.55,
            "created_from_sessions": ["session-other"],
            "times_reused": 0,
            "capture_reason": "The workflow succeeded, has stable inputs, and looks reusable.",
        },
    )
    service = DailyReviewService(
        paths=workspace_paths,
        memory_store=store,
        skill_manager=skill_manager,
        task_manager=TaskManager(workspace_paths.tasks_file),
        trace_recorder=TraceRecorder(workspace_paths),
    )

    result = service.run(date.today())

    assert result.summary_path.exists()
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "Daily Review for" in summary
    assert "## Skill Draft Review" in summary
    assert "Skill draft learning events" in summary
    assert "Daily Agent Profile Reader" in result.promoted_skills
    assert any(item.slug == "daily_agent_profile_reader" for item in result.reviewed_skill_drafts)
    assert any(item.decision == "pending" for item in result.reviewed_skill_drafts)
    assert result.open_questions

    user_profile = workspace_paths.user_profile.read_text(encoding="utf-8")
    assert "Prefers Python tooling" in user_profile
    agent_profile = workspace_paths.agent_profile.read_text(encoding="utf-8")
    assert "Review learned skill drafts during daily consolidation" in agent_profile
    assert "Promote mature skill drafts into published skills" in agent_profile

    promoted_path = workspace_paths.skills_dir / promoted_candidate.path.name
    pending_path = workspace_paths.skill_drafts_dir / pending_candidate.path.name
    assert promoted_path.exists()
    assert not promoted_candidate.path.exists()
    assert pending_path.exists()
