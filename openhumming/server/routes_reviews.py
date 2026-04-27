from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(tags=["reviews"])


class DailyReviewResponse(BaseModel):
    review_date: str
    summary_path: str
    user_updates: list[str]
    agent_updates: list[str]


@router.post("/reviews/daily", response_model=DailyReviewResponse)
def run_daily_review(request: Request) -> DailyReviewResponse:
    result = request.app.state.daily_review_service.run()
    return DailyReviewResponse(
        review_date=result.review_date.isoformat(),
        summary_path=str(result.summary_path),
        user_updates=result.user_updates,
        agent_updates=result.agent_updates,
    )
