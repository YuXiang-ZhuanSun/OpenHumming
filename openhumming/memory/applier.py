from pathlib import Path

from openhumming.memory.models import AppliedMemoryUpdate, MemoryUpdateProposal


class MemoryApplier:
    def __init__(self, *, agent_profile: Path, user_profile: Path) -> None:
        self.agent_profile = agent_profile
        self.user_profile = user_profile

    def apply(self, proposals: list[MemoryUpdateProposal]) -> list[AppliedMemoryUpdate]:
        applied: list[AppliedMemoryUpdate] = []
        for target, path in (
            ("agent", self.agent_profile),
            ("user", self.user_profile),
        ):
            target_proposals = [proposal for proposal in proposals if proposal.target == target]
            if not target_proposals:
                continue
            applied.extend(apply_memory_updates(path, target_proposals))
        return applied


def apply_memory_updates(
    profile_path: Path,
    proposals: list[MemoryUpdateProposal],
) -> list[AppliedMemoryUpdate]:
    if not proposals:
        return []

    existing = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
    updated = existing
    applied: list[AppliedMemoryUpdate] = []

    for section in _ordered_sections(proposals):
        section_proposals = [proposal for proposal in proposals if proposal.section == section]
        updated, section_updates = _apply_section_updates(
            markdown=updated,
            heading=section,
            proposals=section_proposals,
            profile_path=profile_path,
        )
        applied.extend(section_updates)

    if applied:
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(updated.rstrip() + "\n", encoding="utf-8")

    return applied


def _ordered_sections(proposals: list[MemoryUpdateProposal]) -> list[str]:
    seen: set[str] = set()
    sections: list[str] = []
    for proposal in proposals:
        if proposal.section in seen:
            continue
        seen.add(proposal.section)
        sections.append(proposal.section)
    return sections


def _apply_section_updates(
    *,
    markdown: str,
    heading: str,
    proposals: list[MemoryUpdateProposal],
    profile_path: Path,
) -> tuple[str, list[AppliedMemoryUpdate]]:
    before, section_body, remainder, section_exists = _split_section(markdown, heading)
    prefix_text, bullets = _extract_section_parts(section_body)
    applied: list[AppliedMemoryUpdate] = []

    for proposal in _deduplicate_proposals(proposals):
        exact_index = _find_exact_bullet_index(bullets, proposal.content)

        if proposal.operation == "remove":
            target_index = exact_index
            if target_index is None:
                target_index = _find_replace_target_index(heading, bullets, proposal)
            if target_index is None:
                continue
            removed = bullets.pop(target_index)
            applied.append(
                AppliedMemoryUpdate(
                    target=proposal.target,
                    section=heading,
                    content=removed,
                    path=profile_path,
                    operation="remove",
                    replaced=removed,
                )
            )
            continue

        if exact_index is not None:
            continue

        if proposal.operation == "replace":
            target_index = _find_replace_target_index(heading, bullets, proposal)
            if target_index is None:
                bullets.append(proposal.content)
                applied.append(
                    AppliedMemoryUpdate(
                        target=proposal.target,
                        section=heading,
                        content=proposal.content,
                        path=profile_path,
                        operation="replace",
                    )
                )
            else:
                replaced = bullets[target_index]
                bullets[target_index] = proposal.content
                applied.append(
                    AppliedMemoryUpdate(
                        target=proposal.target,
                        section=heading,
                        content=proposal.content,
                        path=profile_path,
                        operation="replace",
                        replaced=replaced,
                    )
                )
            continue

        bullets.append(proposal.content)
        applied.append(
            AppliedMemoryUpdate(
                target=proposal.target,
                section=heading,
                content=proposal.content,
                path=profile_path,
                operation="add",
            )
        )

    if not applied:
        return markdown, []

    rendered_body = _render_section_body(prefix_text, bullets)
    if not section_exists:
        base = markdown.rstrip()
        separator = "\n\n" if base else ""
        return base + f"{separator}{heading}{rendered_body}\n", applied

    return before + heading + rendered_body + remainder, applied


def _split_section(markdown: str, heading: str) -> tuple[str, str, str, bool]:
    if heading not in markdown:
        return markdown, "", "", False

    before, after = markdown.split(heading, maxsplit=1)
    next_heading_index = after.find("\n## ")
    if next_heading_index >= 0:
        section_body = after[:next_heading_index]
        remainder = after[next_heading_index:]
    else:
        section_body = after
        remainder = ""
    return before, section_body, remainder, True


def _extract_section_parts(section_body: str) -> tuple[str, list[str]]:
    prefix_lines: list[str] = []
    bullets: list[str] = []
    for line in section_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullet = stripped[2:].strip()
            if bullet:
                bullets.append(bullet)
            continue
        prefix_lines.append(line.rstrip())
    prefix_text = "\n".join(prefix_lines).strip("\n")
    return prefix_text, _deduplicate_strings(bullets)


def _render_section_body(prefix_text: str, bullets: list[str]) -> str:
    segments: list[str] = []
    if prefix_text.strip():
        segments.append(prefix_text.strip())
    if bullets:
        segments.append("\n".join(f"- {bullet}" for bullet in bullets))
    if not segments:
        return "\n"
    return "\n\n" + "\n\n".join(segments).rstrip()


def _find_exact_bullet_index(bullets: list[str], content: str) -> int | None:
    normalized = content.strip()
    for index, bullet in enumerate(bullets):
        if bullet.strip() == normalized:
            return index
    return None


def _find_replace_target_index(
    heading: str,
    bullets: list[str],
    proposal: MemoryUpdateProposal,
) -> int | None:
    anchor = (proposal.anchor or "").strip().lower()
    if anchor:
        for index, bullet in enumerate(bullets):
            lowered = bullet.lower()
            if lowered == anchor or anchor in lowered:
                return index

    if proposal.category == "interaction_style":
        return 0 if bullets else None
    if proposal.category == "working_style":
        return 0 if bullets else None
    if proposal.category == "tool_reporting":
        for index, bullet in enumerate(bullets):
            lowered = bullet.lower()
            if "tool" in lowered or "工具" in lowered:
                return index

    if heading == "## Interaction Style" and bullets:
        return 0
    if heading == "## Working Style" and bullets:
        return 0
    return None


def _deduplicate_proposals(
    proposals: list[MemoryUpdateProposal],
) -> list[MemoryUpdateProposal]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[MemoryUpdateProposal] = []
    for proposal in proposals:
        signature = (
            proposal.operation,
            proposal.content.strip(),
            proposal.category or "",
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(proposal)
    return unique


def _deduplicate_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique
