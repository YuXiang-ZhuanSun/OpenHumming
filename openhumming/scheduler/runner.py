import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from openhumming.scheduler.manager import TaskManager, TaskRecord
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.paths import WorkspacePaths

if TYPE_CHECKING:
    from openhumming.agent.runtime import AgentRuntime


@dataclass(slots=True)
class TaskRunRecord:
    task_id: str
    session_id: str
    started_at: str
    finished_at: str
    success: bool
    response_preview: str
    error: str | None = None


class TaskRunner:
    def __init__(
        self,
        *,
        task_manager: TaskManager,
        runtime: "AgentRuntime",
        paths: WorkspacePaths,
        trace_recorder: TraceRecorder,
        timezone_name: str = "Asia/Shanghai",
        sync_interval_seconds: int = 30,
    ) -> None:
        self.task_manager = task_manager
        self.runtime = runtime
        self.paths = paths
        self.trace_recorder = trace_recorder
        self.timezone_name = timezone_name
        self.sync_interval_seconds = sync_interval_seconds
        self.scheduler: BackgroundScheduler | None = None

    def start(self) -> None:
        if self.scheduler is not None:
            return

        self.scheduler = BackgroundScheduler(timezone=self.timezone_name)
        self.scheduler.start()
        self.sync_jobs()
        self.scheduler.add_job(
            self.sync_jobs,
            trigger="interval",
            seconds=self.sync_interval_seconds,
            id="openhumming.sync_jobs",
            replace_existing=True,
        )

    def shutdown(self) -> None:
        if self.scheduler is None:
            return
        self.scheduler.shutdown(wait=False)
        self.scheduler = None

    def sync_jobs(self) -> None:
        if self.scheduler is None:
            return

        enabled_tasks = {task.id: task for task in self.enabled_tasks()}
        current_jobs = {
            job.id: job
            for job in self.scheduler.get_jobs()
            if job.id.startswith("openhumming.task.")
        }

        for job_id in list(current_jobs):
            task_id = job_id.removeprefix("openhumming.task.")
            if task_id not in enabled_tasks:
                self.scheduler.remove_job(job_id)

        for task in enabled_tasks.values():
            job_id = f"openhumming.task.{task.id}"
            trigger = CronTrigger.from_crontab(task.schedule, timezone=self.timezone_name)
            self.scheduler.add_job(
                self.run_task,
                trigger=trigger,
                args=[task.id],
                id=job_id,
                replace_existing=True,
            )

    def enabled_tasks(self) -> list[TaskRecord]:
        return [task for task in self.task_manager.list_tasks() if task.enabled]

    def run_task(self, task_id: str) -> TaskRunRecord:
        task = self.task_manager.get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task id: {task_id}")
        return self._execute_task(task)

    def _execute_task(self, task: TaskRecord) -> TaskRunRecord:
        started_at = datetime.now(timezone.utc).isoformat()
        session_id = f"task::{task.id}"

        self.trace_recorder.record(
            "task_started",
            {
                "task_id": task.id,
                "title": task.title,
                "schedule": task.schedule,
            },
        )

        try:
            result = self.runtime.respond(session_id, task.prompt)
            record = TaskRunRecord(
                task_id=task.id,
                session_id=session_id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(),
                success=True,
                response_preview=result.response[:200],
            )
            self.trace_recorder.record(
                "task_completed",
                {
                    "task_id": task.id,
                    "session_id": session_id,
                    "success": True,
                },
            )
        except Exception as exc:
            record = TaskRunRecord(
                task_id=task.id,
                session_id=session_id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(),
                success=False,
                response_preview="",
                error=str(exc),
            )
            self.trace_recorder.record(
                "task_completed",
                {
                    "task_id": task.id,
                    "session_id": session_id,
                    "success": False,
                    "error": str(exc),
                },
            )
            self._record_run(record)
            raise

        self._record_run(record)
        return record

    def _record_run(self, record: TaskRunRecord) -> None:
        destination = self.paths.task_runs_dir / (
            f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
