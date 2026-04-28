from dataclasses import dataclass
from datetime import date
from pathlib import Path

from openhumming.memory.models import MemoryUpdateProposal
from openhumming.memory.review_models import ReviewedSkillDraft
from openhumming.memory.store import MemoryStore
from openhumming.memory.summarizer import build_daily_summary
from openhumming.memory.updater import (
    extract_agent_memory_proposals,
    apply_agent_profile_updates,
    apply_user_profile_updates,
    extract_user_memory_proposals,
)
from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.skills.reviewer import SkillDraftReviewer
from openhumming.trace.recorder import TraceRecorder
from openhumming.workspace.paths import WorkspacePaths


@dataclass(slots=True)
class DailyReviewResult:
    review_date: date
    summary_path: Path
    user_updates: list[str]
    agent_updates: list[str]
    reviewed_skill_drafts: list[ReviewedSkillDraft]
    promoted_skills: list[str]
    open_questions: list[str]


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
        self.skill_draft_reviewer = SkillDraftReviewer()

    def run(self, target_date: date | None = None) -> DailyReviewResult:
        review_date = target_date or date.today()
        messages = self.memory_store.load_messages_for_date(review_date)
        user_proposals = extract_user_memory_proposals(messages)
        reviewed_skill_drafts = self._review_skill_drafts(messages, review_date)
        promoted_skills = [
            item.name for item in reviewed_skill_drafts if item.decision == "promoted"
        ]
        agent_proposals = extract_agent_memory_proposals(messages)
        agent_proposals.extend(
            self._review_capability_proposals(reviewed_skill_drafts, promoted_skills)
        )
        user_updates = apply_user_profile_updates(self.paths.user_profile, user_proposals)
        agent_updates = apply_agent_profile_updates(self.paths.agent_profile, agent_proposals)
        open_questions = [
            f"Review draft {item.name}: {item.reason}"
            for item in reviewed_skill_drafts
            if item.decision != "promoted"
        ]

        summary = build_daily_summary(
            review_date=review_date,
            messages=messages,
            user_updates=user_updates,
            agent_updates=agent_updates,
            reviewed_skill_drafts=reviewed_skill_drafts,
            promoted_skills=promoted_skills,
            open_questions=open_questions,
            turn_memory_update_count=self._count_turn_memory_updates(messages),
            drafts_created_count=self._count_created_skill_drafts(messages),
            task_run_count=self._count_task_runs(review_date),
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
                "reviewed_skill_drafts": len(reviewed_skill_drafts),
                "promoted_skills": promoted_skills,
                "open_questions": open_questions,
            },
        )

        return DailyReviewResult(
            review_date=review_date,
            summary_path=summary_path,
            user_updates=user_updates,
            agent_updates=agent_updates,
            reviewed_skill_drafts=reviewed_skill_drafts,
            promoted_skills=promoted_skills,
            open_questions=open_questions,
        )

    def _review_skill_drafts(
        self,
        messages,
        review_date: date,
    ) -> list[ReviewedSkillDraft]:
        review_date = review_date
        touched_sessions = {message.session_id for message in messages}
        reviewed: list[ReviewedSkillDraft] = []
        for draft in self.skill_manager.list_skill_drafts():
            created_sessions = draft.metadata.get("created_from_sessions") or []
            touched_today = any(session_id in touched_sessions for session_id in created_sessions)
            published_skill_exists = (
                self.skill_manager.get_skill(draft.name) is not None
                or self.skill_manager.get_skill(draft.slug) is not None
            )
            decision = self.skill_draft_reviewer.review(
                draft,
                touched_today=touched_today,
                published_skill_exists=published_skill_exists,
            )

            promoted_path = None
            if decision.decision == "promoted":
                promoted = self.skill_manager.promote_skill_draft(
                    draft.slug,
                    metadata={
                        "promoted_on": review_date.isoformat(),
                        "promoted_by": "daily_review",
                        "promotion_reason": decision.reason,
                    },
                )
                promoted_path = promoted.path if promoted is not None else None

            reviewed.append(
                ReviewedSkillDraft(
                    name=draft.name,
                    slug=draft.slug,
                    decision=decision.decision,
                    reason=decision.reason,
                    confidence=decision.confidence,
                    source_path=draft.path,
                    promoted_path=promoted_path,
                )
            )
        return reviewed

    def _count_turn_memory_updates(self, messages) -> int:
        count = 0
        for message in messages:
            if message.role != "assistant":
                continue
            updates = message.metadata.get("memory_updates", [])
            if isinstance(updates, list):
                count += len(updates)
        return count

    def _count_created_skill_drafts(self, messages) -> int:
        count = 0
        for message in messages:
            if message.role != "assistant":
                continue
            if message.metadata.get("created_skill_draft") is not None:
                count += 1
        return count

    def _count_task_runs(self, review_date: date) -> int:
        run_file = self.paths.task_runs_dir / f"{review_date.isoformat()}.jsonl"
        if not run_file.exists():
            return 0
        return len([line for line in run_file.read_text(encoding="utf-8").splitlines() if line.strip()])

    def _review_capability_proposals(
        self,
        reviewed_skill_drafts: list[ReviewedSkillDraft],
        promoted_skills: list[str],
    ) -> list[MemoryUpdateProposal]:
        proposals: list[MemoryUpdateProposal] = []
        if reviewed_skill_drafts:
            proposals.append(
                MemoryUpdateProposal(
                    target="agent",
                    section="## Capabilities",
                    content="Review learned skill drafts during daily consolidation",
                    reason="The agent reviewed skill drafts during the daily review loop.",
                    confidence=0.73,
                )
            )
        if promoted_skills:
            proposals.append(
                MemoryUpdateProposal(
                    target="agent",
                    section="## Capabilities",
                    content="Promote mature skill drafts into published skills",
                    reason="The agent promoted stable skill drafts during the daily review loop.",
                    confidence=0.77,
                )
            )
        return proposals
