from pathlib import Path

from openhumming.memory.applier import apply_memory_updates
from openhumming.memory.conversation import StoredMessage
from openhumming.memory.models import MemoryUpdateProposal
from openhumming.memory.reflection import MemoryReflectionEngine


def extract_user_memory_proposals(
    messages: list[StoredMessage],
) -> list[MemoryUpdateProposal]:
    engine = MemoryReflectionEngine()
    proposals: list[MemoryUpdateProposal] = []
    for message in messages:
        if message.role != "user":
            continue
        proposals.extend(
            proposal
            for proposal in engine.propose_from_message(message.content)
            if proposal.target == "user"
        )
    return _deduplicate(proposals)


def extract_agent_memory_proposals(
    messages: list[StoredMessage],
) -> list[MemoryUpdateProposal]:
    engine = MemoryReflectionEngine()
    proposals: list[MemoryUpdateProposal] = []
    assistant_turns = [message for message in messages if message.role == "assistant"]

    for message in messages:
        if message.role != "user":
            continue
        proposals.extend(
            proposal
            for proposal in engine.propose_from_message(message.content)
            if proposal.target == "agent"
        )

    if any(message.metadata.get("created_skill_draft") for message in assistant_turns):
        proposals.append(
            MemoryUpdateProposal(
                target="agent",
                section="## Capabilities",
                content="Capture successful workflows as reviewable skill drafts",
                reason="The runtime created skill drafts from completed work during the day.",
                confidence=0.74,
            )
        )

    if any("task_create" in message.metadata.get("tool_actions", []) for message in assistant_turns):
        proposals.append(
            MemoryUpdateProposal(
                target="agent",
                section="## Capabilities",
                content="Turn recurring prompts into scheduled tasks",
                reason="The runtime created scheduled tasks from natural-language requests.",
                confidence=0.72,
            )
        )

    if any(message.metadata.get("memory_updates") for message in assistant_turns):
        proposals.append(
            MemoryUpdateProposal(
                target="agent",
                section="## Capabilities",
                content="Refine durable agent and user memory during live conversations",
                reason="The runtime updated durable memory during the active conversation loop.",
                confidence=0.71,
            )
        )

    return _deduplicate(proposals)


def apply_user_profile_updates(
    profile_path: Path,
    proposals: list[MemoryUpdateProposal],
) -> list[str]:
    return [update.content for update in apply_memory_updates(profile_path, proposals)]


def apply_agent_profile_updates(
    profile_path: Path,
    proposals: list[MemoryUpdateProposal],
) -> list[str]:
    return [update.content for update in apply_memory_updates(profile_path, proposals)]


def is_stable_memory_candidate(text: str) -> bool:
    lowered = text.lower()
    return any(
        keyword in lowered
        for keyword in ("prefer", "always", "长期", "偏好", "记住", "from now on")
    )


def _deduplicate(
    proposals: list[MemoryUpdateProposal],
) -> list[MemoryUpdateProposal]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[MemoryUpdateProposal] = []
    for proposal in proposals:
        signature = (
            proposal.target,
            proposal.section,
            proposal.content,
            proposal.operation,
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(proposal)
    return unique
