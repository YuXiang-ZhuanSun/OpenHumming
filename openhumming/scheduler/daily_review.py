from datetime import date


def build_daily_review_prompt(target_date: date | None = None) -> str:
    resolved_date = target_date or date.today()
    return (
        f"Summarize the conversations for {resolved_date.isoformat()} and update "
        "memory or skills if the learnings are stable and reusable."
    )
