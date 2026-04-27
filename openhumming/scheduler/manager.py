import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from openhumming.scheduler.parser import ParsedSchedule, parse_schedule_text


@dataclass(slots=True)
class TaskRecord:
    id: str
    title: str
    prompt: str
    schedule: str
    enabled: bool
    created_at: str
    natural_language: str


class TaskManager:
    def __init__(self, tasks_file: Path) -> None:
        self.tasks_file = tasks_file
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tasks_file.exists():
            self.tasks_file.write_text("[]\n", encoding="utf-8")

    def list_tasks(self) -> list[TaskRecord]:
        raw_items = json.loads(self.tasks_file.read_text(encoding="utf-8") or "[]")
        return [TaskRecord(**item) for item in raw_items]

    def get_task(self, task_id: str) -> TaskRecord | None:
        for task in self.list_tasks():
            if task.id == task_id:
                return task
        return None

    def create_from_text(
        self,
        natural_language: str,
        prompt: str | None = None,
        title: str | None = None,
    ) -> TaskRecord:
        parsed = parse_schedule_text(natural_language)
        return self.create_task(
            parsed=parsed,
            natural_language=natural_language,
            prompt_override=prompt,
            title_override=title,
        )

    def create_task(
        self,
        *,
        parsed: ParsedSchedule,
        natural_language: str,
        prompt_override: str | None = None,
        title_override: str | None = None,
    ) -> TaskRecord:
        record = TaskRecord(
            id=f"task_{uuid4().hex[:8]}",
            title=title_override or parsed.title,
            prompt=prompt_override or parsed.prompt,
            schedule=parsed.cron,
            enabled=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            natural_language=natural_language,
        )
        items = self.list_tasks()
        items.append(record)
        self.tasks_file.write_text(
            json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        return record
