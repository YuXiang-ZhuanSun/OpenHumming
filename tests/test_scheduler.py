from openhumming.scheduler.manager import TaskManager
from openhumming.scheduler.parser import parse_schedule_text


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
