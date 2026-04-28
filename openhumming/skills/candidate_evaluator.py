from dataclasses import dataclass

from openhumming.skills.workflow_capture import WorkflowCapture

EXPLICIT_DRAFT_HINTS = (
    "create skill",
    "turn this into a skill",
    "turn this workflow into skill",
    "turn this workflow into a skill",
    "summarize as a skill",
    "\u6c89\u6dc0\u6210",
    "\u56fa\u5316",
    "\u603b\u7ed3\u6210 skill",
)
REUSE_HINTS = (
    "next time",
    "repeat",
    "reusable",
    "workflow",
    "\u4e0b\u6b21\u4e5f\u8fd9\u4e48\u505a",
    "\u91cd\u590d",
    "\u6d41\u7a0b",
)
STABLE_INPUT_KEYS = {"path", "name", "slug", "natural_language", "title", "prompt"}


@dataclass(slots=True)
class SkillCandidateAssessment:
    should_create_draft: bool
    reason: str
    confidence: float


class SkillCandidateEvaluator:
    def evaluate(self, capture: WorkflowCapture) -> SkillCandidateAssessment:
        lowered_goal = capture.user_goal.lower()
        explicit_hint = any(hint in lowered_goal for hint in EXPLICIT_DRAFT_HINTS)
        reuse_hint = any(hint in lowered_goal for hint in REUSE_HINTS)
        stable_inputs = bool(capture.input_keys & STABLE_INPUT_KEYS)
        multi_step = len(capture.steps) >= 2 or len(capture.plan_notes) >= 2
        successful = capture.completed and bool(capture.successful_steps)

        if explicit_hint and successful:
            return SkillCandidateAssessment(
                should_create_draft=True,
                reason="The user explicitly asked to retain the finished workflow as a skill.",
                confidence=0.92,
            )
        if successful and stable_inputs and (multi_step or reuse_hint):
            return SkillCandidateAssessment(
                should_create_draft=True,
                reason="The workflow succeeded, has stable inputs, and looks reusable.",
                confidence=0.78 if multi_step else 0.71,
            )
        if not successful:
            return SkillCandidateAssessment(
                should_create_draft=False,
                reason="The workflow did not complete successfully enough to be learned.",
                confidence=0.18,
            )
        return SkillCandidateAssessment(
            should_create_draft=False,
            reason="The workflow looks too narrow or underspecified to draft as a reusable skill yet.",
            confidence=0.34,
        )
