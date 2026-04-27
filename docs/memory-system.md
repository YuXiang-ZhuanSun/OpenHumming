# Memory System

OpenHumming uses markdown for stable memory and JSONL for conversational logs.

- `workspace/agent.md`: long-lived agent identity and principles
- `workspace/user.md`: durable user preferences and project context
- `workspace/conversations/*.jsonl`: turn-level history
- `workspace/summaries/*.md`: future daily or session summaries

The MVP reads profiles on every turn and appends each completed turn to the
daily conversation log.
