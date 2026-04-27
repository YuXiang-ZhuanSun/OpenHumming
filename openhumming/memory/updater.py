import re
from dataclasses import dataclass
from pathlib import Path

from openhumming.memory.conversation import StoredMessage

USER_PREFERENCE_PATTERNS = (
    re.compile(r"(?:remember(?: that)?|i prefer|i like)\s+([^.!?\n]+)", re.IGNORECASE),
    re.compile(
        r"(?:\u8bb0\u4f4f\u6211(?:\u7684)?(?:\u504f\u597d|\u559c\u6b22)?|\u6211(?:\u504f\u597d|\u559c\u6b22|\u66f4\u559c\u6b22))([^。！\n]+)"
    ),
)
AGENT_CAPABILITIES = (
    "Execute scheduled tasks",
    "Create skills from repeated workflows",
    "Review daily conversations and update memory",
)


@dataclass(slots=True)
class MemoryUpdateProposal:
    target: str
    content: str
    reason: str


def extract_user_memory_proposals(
    messages: list[StoredMessage],
) -> list[MemoryUpdateProposal]:
    proposals: list[MemoryUpdateProposal] = []
    seen: set[str] = set()
    for message in messages:
        if message.role != "user":
            continue
        for pattern in USER_PREFERENCE_PATTERNS:
            for match in pattern.findall(message.content):
                normalized = _normalize_preference(match)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                proposals.append(
                    MemoryUpdateProposal(
                        target="user",
                        content=normalized,
                        reason="Explicit long-term user preference detected in conversation.",
                    )
                )
    return proposals


def apply_user_profile_updates(
    profile_path: Path,
    proposals: list[MemoryUpdateProposal],
) -> list[str]:
    content = profile_path.read_text(encoding="utf-8")
    additions = [proposal.content for proposal in proposals if proposal.content not in content]
    if not additions:
        return []

    updated = _append_unique_bullets(content, "## Preferences", additions)
    profile_path.write_text(updated, encoding="utf-8")
    return additions


def apply_agent_profile_updates(profile_path: Path) -> list[str]:
    content = profile_path.read_text(encoding="utf-8")
    additions = [item for item in AGENT_CAPABILITIES if item not in content]
    if not additions:
        return []

    updated = _append_unique_bullets(content, "## Capabilities", additions)
    profile_path.write_text(updated, encoding="utf-8")
    return additions


def is_stable_memory_candidate(text: str) -> bool:
    lowered = text.lower()
    return any(
        keyword in lowered
        for keyword in ("prefer", "always", "\u957f\u671f", "\u504f\u597d", "\u8bb0\u4f4f")
    )


def _normalize_preference(value: str) -> str:
    cleaned = value.strip(" 。.!?\n")
    if not cleaned:
        return ""
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        if cleaned.startswith("\u504f\u597d"):
            return cleaned
        return f"\u504f\u597d {cleaned}".strip()
    if cleaned.lower().startswith("prefer "):
        return cleaned
    return f"Prefers {cleaned}"


def _append_unique_bullets(markdown: str, heading: str, bullets: list[str]) -> str:
    if heading not in markdown:
        bullet_block = "\n".join(f"- {bullet}" for bullet in bullets)
        return markdown.rstrip() + f"\n\n{heading}\n\n{bullet_block}\n"

    before, after = markdown.split(heading, maxsplit=1)
    current_section = after
    next_heading_index = after.find("\n## ")
    if next_heading_index >= 0:
        section_body = after[:next_heading_index]
        remainder = after[next_heading_index:]
    else:
        section_body = after
        remainder = ""

    updated_section = section_body.rstrip()
    for bullet in bullets:
        marker = f"- {bullet}"
        if marker not in updated_section:
            updated_section += f"\n{marker}"

    return before + heading + updated_section + remainder
