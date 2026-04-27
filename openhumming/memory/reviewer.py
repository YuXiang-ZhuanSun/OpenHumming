from dataclasses import dataclass
from datetime import date
from pathlib import Path

from openhumming.memory.store import MemoryStore
from openhumming.memory.summarizer import build_daily_summary
from openhumming.memory.updater import (
    apply_agent_profile_updates,
    apply_user_profile_updates,
    extract_user_memory_proposals,
)
from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.paths import WorkspacePaths


@dataclass(slots=True)
class DailyReviewResult:
    review_date: date
    summary_path: Path
    user_updates: list[str]
    agent_updates: list[str]


class DailyReviewService:
    def __init__(
        self,
        *,
        paths: WorkspacePaths,
        memory_store: MemoryStore,
        skill_manager: SkillManager,
        task_manager: TaskManager,
        trace_recorder: TraceRecorder,
    ) -> None:
        self.paths = paths
        self.memory_store = memory_store
        self.skill_manager = skill_manager
        self.task_manager = task_manager
        self.trace_recorder = trace_recorder

    def run(self, target_date: date | None = None) -> DailyReviewResult:
        review_date = target_date or date.today()
        messages = self.memory_store.load_messages_for_date(review_date)
        user_proposals = extract_user_memory_proposals(messages)
        user_updates = apply_user_profile_updates(self.paths.user_profile, user_proposals)
        agent_updates = apply_agent_profile_updates(self.paths.agent_profile)

        summary = build_daily_summary(
            review_date=review_date,
            messages=messages,
            user_updates=user_updates,
            agent_updates=agent_updates,
            skill_count=len(self.skill_manager.list_skills()),
            task_count=len(self.task_manager.list_tasks()),
        )
        summary_path = self.paths.summary_file(review_date)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")

        self.trace_recorder.record(
            "daily_review_completed",
            {
                "date": review_date.isoformat(),
                "summary_path": str(summary_path),
                "user_updates": user_updates,
                "agent_updates": agent_updates,
            },
        )

        return DailyReviewResult(
            review_date=review_date,
            summary_path=summary_path,
            user_updates=user_updates,
            agent_updates=agent_updates,
        )
