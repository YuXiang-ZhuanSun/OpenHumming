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


def test_daily_review_writes_summary_and_updates_memory(workspace_paths) -> None:
    store = MemoryStore(workspace_paths)
    store.save_turn(
        "session-review",
        "请记住我偏好 Python 工具链",
        "我会记住这个偏好。",
        metadata={"intent": "chat"},
    )
    service = DailyReviewService(
        paths=workspace_paths,
        memory_store=store,
        skill_manager=SkillManager(workspace_paths.skills_dir),
        task_manager=TaskManager(workspace_paths.tasks_file),
        trace_recorder=TraceRecorder(workspace_paths),
    )

    result = service.run(date.today())

    assert result.summary_path.exists()
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "Daily Review for" in summary
    user_profile = workspace_paths.user_profile.read_text(encoding="utf-8")
    assert "偏好 Python 工具链" in user_profile
    agent_profile = workspace_paths.agent_profile.read_text(encoding="utf-8")
    assert "Review daily conversations and update memory" in agent_profile
