from dataclasses import dataclass

from openhumming.skills.loader import SkillDocument


@dataclass(slots=True)
class SkillDraftReviewDecision:
    decision: str
    reason: str
    confidence: float


class SkillDraftReviewer:
    def review(
        self,
        draft: SkillDocument,
        *,
        touched_today: bool,
        published_skill_exists: bool,
    ) -> SkillDraftReviewDecision:
        confidence = float(draft.metadata.get("confidence") or 0.0)
        times_reused = int(draft.metadata.get("times_reused") or 0)
        capture_reason = str(draft.metadata.get("capture_reason") or "")
        explicit_request = "explicitly asked" in capture_reason.lower()

        if published_skill_exists:
            return SkillDraftReviewDecision(
                decision="pending",
                reason="A published skill with the same name already exists, so this draft was not promoted.",
                confidence=0.24,
            )

        if explicit_request and confidence >= 0.85:
            return SkillDraftReviewDecision(
                decision="promoted",
                reason="The draft came from an explicit user request and has high capture confidence.",
                confidence=confidence,
            )

        if times_reused >= 1 and confidence >= 0.7:
            return SkillDraftReviewDecision(
                decision="promoted",
                reason="The draft has already shown signs of reuse and is stable enough to publish.",
                confidence=confidence,
            )

        if touched_today and confidence >= 0.78:
            return SkillDraftReviewDecision(
                decision="promoted",
                reason="The draft was created from today's work and has enough confidence to publish.",
                confidence=confidence,
            )

        return SkillDraftReviewDecision(
            decision="pending",
            reason="The draft still needs more confidence, reuse, or explicit confirmation before promotion.",
            confidence=max(confidence, 0.34),
        )
