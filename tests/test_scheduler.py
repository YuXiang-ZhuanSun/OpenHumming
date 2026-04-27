import json

from openhumming.agent.runtime import AgentRuntime
from openhumming.llm import build_provider
from openhumming.scheduler.manager import TaskManager
from openhumming.scheduler.parser import parse_schedule_text
from openhumming.scheduler.runner import TaskRunner
from openhumming.memory.store import MemoryStore
from openhumming.skills.manager import SkillManager
from openhumming.tools import build_default_registry
from openhumming.trace.recorder import TraceRecorder


def test_parse_daily_schedule_text() -> None:
    parsed = parse_schedule_text("每天晚上 11 点总结今天的对话")

    assert parsed.cron == "0 23 * * *"
    assert parsed.prompt == "总结今天的对话"


def test_task_manager_persists_tasks(workspace_paths) -> None:
    manager = TaskManager(workspace_paths.tasks_file)
    task = manager.create_from_text("每周一 上午 9 点整理 skills")
    stored = manager.list_tasks()

    assert task.schedule == "0 9 * * 1"
    assert len(stored) == 1
    assert stored[0].id == task.id


def test_task_runner_executes_task_and_records_run(settings, workspace_paths) -> None:
    manager = TaskManager(workspace_paths.tasks_file)
    task = manager.create_from_text("每天晚上 11 点总结今天的对话")
    skill_manager = SkillManager(workspace_paths.skills_dir)
    runtime = AgentRuntime(
        settings=settings,
        memory_store=MemoryStore(workspace_paths),
        provider=build_provider(settings),
        trace_recorder=TraceRecorder(workspace_paths),
        skill_manager=skill_manager,
        tool_registry=build_default_registry(workspace_paths, skill_manager, manager),
    )
    runner = TaskRunner(
        task_manager=manager,
        runtime=runtime,
        paths=workspace_paths,
        trace_recorder=TraceRecorder(workspace_paths),
        timezone_name="Asia/Shanghai",
        sync_interval_seconds=300,
    )

    record = runner.run_task(task.id)

    assert record.success is True
    run_file = next(workspace_paths.task_runs_dir.glob("*.jsonl"))
    run_records = [json.loads(line) for line in run_file.read_text(encoding="utf-8").splitlines()]
    assert run_records[0]["task_id"] == task.id
    assert run_records[0]["success"] is True
