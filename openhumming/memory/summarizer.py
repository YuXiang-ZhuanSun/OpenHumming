from datetime import date

from openhumming.memory.store import MemoryContext


def summarize_context(context: MemoryContext, target_date: date | None = None) -> str:
    resolved_date = target_date or date.today()
    return (
        f"# Summary for {resolved_date.isoformat()}\n\n"
        f"- Agent profile loaded: {bool(context.agent_profile)}\n"
        f"- User profile loaded: {bool(context.user_profile)}\n"
        f"- Conversation messages considered: {len(context.conversation_history)}\n"
    )
