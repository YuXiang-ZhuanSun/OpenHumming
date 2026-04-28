from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "WorkspacePaths":
        return cls(Path(root).resolve())

    @property
    def agent_profile(self) -> Path:
        return self.root / "agent.md"

    @property
    def user_profile(self) -> Path:
        return self.root / "user.md"

    @property
    def conversations_dir(self) -> Path:
        return self.root / "conversations"

    @property
    def summaries_dir(self) -> Path:
        return self.root / "summaries"

    @property
    def skills_dir(self) -> Path:
        return self.root / "skills"

    @property
    def skill_drafts_dir(self) -> Path:
        return self.skills_dir / "drafts"

    @property
    def tasks_dir(self) -> Path:
        return self.root / "tasks"

    @property
    def task_runs_dir(self) -> Path:
        return self.tasks_dir / "runs"

    @property
    def tasks_file(self) -> Path:
        return self.tasks_dir / "tasks.json"

    @property
    def files_dir(self) -> Path:
        return self.root / "files"

    @property
    def traces_dir(self) -> Path:
        return self.root / "traces"

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def provider_settings_file(self) -> Path:
        return self.config_dir / "provider_settings.json"

    @property
    def directories(self) -> tuple[Path, ...]:
        return (
            self.root,
            self.conversations_dir,
            self.summaries_dir,
            self.skills_dir,
            self.skill_drafts_dir,
            self.tasks_dir,
            self.task_runs_dir,
            self.files_dir,
            self.traces_dir,
            self.config_dir,
        )

    def conversation_file(self, target_date: date | None = None) -> Path:
        resolved_date = target_date or date.today()
        return self.conversations_dir / f"{resolved_date.isoformat()}.jsonl"

    def summary_file(self, target_date: date | None = None) -> Path:
        resolved_date = target_date or date.today()
        return self.summaries_dir / f"{resolved_date.isoformat()}.md"

    def trace_file(self, target_date: date | None = None) -> Path:
        resolved_date = target_date or date.today()
        return self.traces_dir / f"{resolved_date.isoformat()}.jsonl"
