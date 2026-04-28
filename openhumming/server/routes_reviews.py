from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(tags=["reviews"])


class ReviewedSkillDraftResponse(BaseModel):
    name: str
    slug: str
    decision: str
    reason: str
    confidence: float
    source_path: str
    promoted_path: str | None = None


class DailyReviewResponse(BaseModel):
    review_date: str
    summary_path: str
    user_updates: list[str]
    agent_updates: list[str]
    reviewed_skill_drafts: list[ReviewedSkillDraftResponse]
    promoted_skills: list[str]
    open_questions: list[str]


@router.post("/reviews/daily", response_model=DailyReviewResponse)
def run_daily_review(request: Request) -> DailyReviewResponse:
    result = request.app.state.daily_review_service.run()
    return DailyReviewResponse(
        review_date=result.review_date.isoformat(),
        summary_path=str(result.summary_path),
        user_updates=result.user_updates,
        agent_updates=result.agent_updates,
        reviewed_skill_drafts=[
            ReviewedSkillDraftResponse(
                name=item.name,
                slug=item.slug,
                decision=item.decision,
                reason=item.reason,
                confidence=item.confidence,
                source_path=str(item.source_path),
                promoted_path=str(item.promoted_path) if item.promoted_path else None,
            )
            for item in result.reviewed_skill_drafts
        ],
        promoted_skills=result.promoted_skills,
        open_questions=result.open_questions,
    )
