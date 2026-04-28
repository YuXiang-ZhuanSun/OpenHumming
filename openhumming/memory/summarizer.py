from datetime import date

from openhumming.memory.review_models import ReviewedSkillDraft
from openhumming.memory.conversation import StoredMessage


def build_daily_summary(
    *,
    review_date: date,
    messages: list[StoredMessage],
    user_updates: list[str],
    agent_updates: list[str],
    reviewed_skill_drafts: list[ReviewedSkillDraft],
    promoted_skills: list[str],
    open_questions: list[str],
    turn_memory_update_count: int,
    drafts_created_count: int,
    task_run_count: int,
    skill_count: int,
    task_count: int,
) -> str:
    session_count = len({message.session_id for message in messages})
    user_messages = [message for message in messages if message.role == "user"]
    assistant_messages = [message for message in messages if message.role == "assistant"]
    recent_topics = _recent_topics(user_messages)

    summary_lines = [
        f"# Daily Review for {review_date.isoformat()}",
        "",
        "## Activity",
        "",
        f"- Total messages: {len(messages)}",
        f"- User messages: {len(user_messages)}",
        f"- Assistant messages: {len(assistant_messages)}",
        f"- Sessions touched: {session_count}",
        f"- Skills available: {skill_count}",
        f"- Scheduled tasks: {task_count}",
        f"- Task runs recorded today: {task_run_count}",
        f"- Turn-level memory writes observed: {turn_memory_update_count}",
        f"- Skill draft learning events: {drafts_created_count}",
        "",
        "## Recent Topics",
        "",
    ]

    if recent_topics:
        summary_lines.extend(f"- {topic}" for topic in recent_topics)
    else:
        summary_lines.append("- No user topics were recorded today.")

    summary_lines.extend(
        [
            "",
            "## Memory Updates",
            "",
            f"- User profile updates: {len(user_updates)}",
            f"- Agent profile updates: {len(agent_updates)}",
        ]
    )

    if user_updates:
        summary_lines.extend(["", "### User Profile Additions", ""])
        summary_lines.extend(f"- {item}" for item in user_updates)

    if agent_updates:
        summary_lines.extend(["", "### Agent Profile Additions", ""])
        summary_lines.extend(f"- {item}" for item in agent_updates)

    summary_lines.extend(
        [
            "",
            "## Skill Draft Review",
            "",
            f"- Drafts reviewed: {len(reviewed_skill_drafts)}",
            f"- Drafts promoted: {len(promoted_skills)}",
            f"- Drafts still pending: {len([item for item in reviewed_skill_drafts if item.decision != 'promoted'])}",
        ]
    )

    if promoted_skills:
        summary_lines.extend(["", "### Promoted Skills", ""])
        summary_lines.extend(f"- {item}" for item in promoted_skills)

    pending_drafts = [item for item in reviewed_skill_drafts if item.decision != "promoted"]
    if pending_drafts:
        summary_lines.extend(["", "### Drafts Still Pending", ""])
        summary_lines.extend(
            f"- {item.name}: {item.reason} (confidence {item.confidence:.2f})"
            for item in pending_drafts
        )

    summary_lines.extend(["", "## Open Questions", ""])
    if open_questions:
        summary_lines.extend([""] + [f"- {item}" for item in open_questions])
    else:
        summary_lines.extend(["", "- No open review questions today."])

    return "\n".join(summary_lines).rstrip() + "\n"


def _recent_topics(user_messages: list[StoredMessage]) -> list[str]:
    topics: list[str] = []
    for message in user_messages[-5:]:
        cleaned = " ".join(message.content.split())
        if len(cleaned) > 90:
            cleaned = cleaned[:87].rstrip() + "..."
        topics.append(cleaned)
    return topics
