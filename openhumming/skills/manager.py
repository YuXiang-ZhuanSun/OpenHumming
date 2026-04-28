import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openhumming.skills.creator import SkillCreator, slugify
from openhumming.skills.loader import SkillDocument, load_all_skills, load_skill_file
from openhumming.skills.validator import validate_skill_markdown

if TYPE_CHECKING:
    from openhumming.skills.extractor import SkillDraft


class SkillManager:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.drafts_dir = skills_dir / "drafts"
        self.creator = SkillCreator(
            Path(__file__).resolve().parent / "templates" / "skill_template.md"
        )

    def list_skills(self) -> list[SkillDocument]:
        return load_all_skills(self.skills_dir, exclude_dir_names={"drafts"})

    def list_skill_drafts(self) -> list[SkillDocument]:
        return load_all_skills(self.drafts_dir)

    def get_skill(self, name_or_slug: str) -> SkillDocument | None:
        target = name_or_slug.strip().lower()
        for skill in self.list_skills():
            if skill.slug.lower() == target or skill.name.lower() == target:
                return skill
        return None

    def get_skill_draft(self, name_or_slug: str) -> SkillDocument | None:
        target = name_or_slug.strip().lower()
        for skill in self.list_skill_drafts():
            if skill.slug.lower() == target or skill.name.lower() == target:
                return skill
        return None

    def find_relevant_skills(self, user_message: str, limit: int = 3) -> list[SkillDocument]:
        scored: list[tuple[int, SkillDocument]] = []
        for skill in self.list_skills():
            score = self._score_skill(skill, user_message)
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda item: (-item[0], item[1].name.lower()))
        return [skill for _, skill in scored[:limit]]

    def create_skill(
        self,
        *,
        name: str,
        description: str,
        when_to_use: str,
        inputs: list[str],
        procedure: list[str],
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> SkillDocument:
        return self._create_document(
            destination=self.skills_dir,
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
            metadata=metadata,
        )

    def create_skill_draft(
        self,
        *,
        name: str,
        description: str,
        when_to_use: str,
        inputs: list[str],
        procedure: list[str],
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> SkillDocument:
        draft_metadata = {"status": "draft", **(metadata or {})}
        return self._create_document(
            destination=self.drafts_dir,
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
            metadata=draft_metadata,
        )

    def refresh_skill_draft(
        self,
        name_or_slug: str,
        *,
        draft: "SkillDraft",
    ) -> SkillDocument | None:
        existing = self.get_skill_draft(name_or_slug)
        if existing is None:
            return None
        merged_metadata = self._merge_draft_metadata(existing.metadata, draft.metadata)
        return self._write_document(
            path=existing.path,
            name=draft.name,
            description=draft.description,
            when_to_use=draft.when_to_use,
            inputs=draft.inputs,
            procedure=draft.procedure,
            output=draft.output,
            metadata=merged_metadata,
        )

    def promote_skill_draft(
        self,
        name_or_slug: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> SkillDocument | None:
        draft = self.get_skill_draft(name_or_slug)
        if draft is None:
            return None
        if self.get_skill(name_or_slug) is not None or self.get_skill(draft.slug) is not None:
            raise ValueError(f"Published skill already exists for: {name_or_slug}")

        merged_metadata = {
            **draft.metadata,
            **(metadata or {}),
            "status": "published",
        }
        path = self.skills_dir / draft.path.name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self._replace_frontmatter(draft.content, merged_metadata),
            encoding="utf-8",
        )
        draft.path.unlink(missing_ok=True)
        return load_skill_file(path)

    def _create_document(
        self,
        *,
        destination: Path,
        name: str,
        description: str,
        when_to_use: str,
        inputs: list[str],
        procedure: list[str],
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> SkillDocument:
        slug = slugify(name)
        path = destination / f"{slug}.md"
        return self._write_document(
            path=path,
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
            metadata=metadata,
        )

    def _score_skill(self, skill: SkillDocument, user_message: str) -> int:
        lowered_message = user_message.lower()
        score = 0

        if skill.name.lower() in lowered_message:
            score += 20
        if skill.slug.lower() in lowered_message:
            score += 18

        name_tokens = self._tokens(skill.name)
        description_tokens = self._tokens(skill.description)
        content_tokens = self._tokens(skill.content)
        query_tokens = self._tokens(user_message)

        for token in query_tokens:
            if token in name_tokens:
                score += 8
            elif token in description_tokens:
                score += 5
            elif token in content_tokens:
                score += 2

        if self._contains_chinese_query_overlap(user_message, skill):
            score += 6

        return score

    def _tokens(self, value: str) -> set[str]:
        return {token.lower() for token in re.findall(r"[A-Za-z0-9_]{2,}", value)}

    def _contains_chinese_query_overlap(
        self,
        user_message: str,
        skill: SkillDocument,
    ) -> bool:
        chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,}", user_message)
        if not chinese_terms:
            return False
        haystack = f"{skill.name}\n{skill.description}\n{skill.content}"
        return any(term in haystack for term in chinese_terms)

    def _replace_frontmatter(self, content: str, metadata: dict[str, Any]) -> str:
        body = content.strip()
        if body.startswith("---\n"):
            closing_index = body.find("\n---\n", 4)
            if closing_index >= 0:
                body = body[closing_index + 5 :].strip()
        return self.creator.render_frontmatter(metadata) + "\n" + body.rstrip() + "\n"

    def _write_document(
        self,
        *,
        path: Path,
        name: str,
        description: str,
        when_to_use: str,
        inputs: list[str],
        procedure: list[str],
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> SkillDocument:
        content = self.creator.render(
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
            metadata=metadata,
        )
        valid, errors = validate_skill_markdown(content)
        if not valid:
            raise ValueError(f"Invalid skill markdown: {', '.join(errors)}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return load_skill_file(path)

    def _merge_draft_metadata(
        self,
        existing_metadata: dict[str, Any],
        incoming_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        existing_sessions = self._coerce_session_list(
            existing_metadata.get("created_from_sessions")
        )
        incoming_sessions = self._coerce_session_list(
            incoming_metadata.get("created_from_sessions")
        )
        new_sessions = [
            session_id for session_id in incoming_sessions if session_id not in existing_sessions
        ]
        times_reused = int(existing_metadata.get("times_reused") or 0)
        if new_sessions:
            times_reused += len(new_sessions)

        confidence = max(
            float(existing_metadata.get("confidence") or 0.0),
            float(incoming_metadata.get("confidence") or 0.0),
        )
        capture_reason = self._merge_capture_reason(
            str(existing_metadata.get("capture_reason") or ""),
            str(incoming_metadata.get("capture_reason") or ""),
        )

        merged = {**existing_metadata, **incoming_metadata}
        merged["status"] = "draft"
        merged["source"] = (
            incoming_metadata.get("source")
            or existing_metadata.get("source")
            or "workflow_capture"
        )
        merged["created_from_sessions"] = existing_sessions + new_sessions
        merged["confidence"] = round(confidence, 2)
        merged["times_reused"] = times_reused
        if capture_reason:
            merged["capture_reason"] = capture_reason
        return merged

    def _coerce_session_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        sessions: list[str] = []
        for item in value:
            session_id = str(item).strip()
            if session_id and session_id not in sessions:
                sessions.append(session_id)
        return sessions

    def _merge_capture_reason(self, existing: str, incoming: str) -> str:
        if existing and incoming and existing != incoming:
            if "explicit" in incoming.lower() and "explicit" not in existing.lower():
                return incoming
            return existing
        return incoming or existing
