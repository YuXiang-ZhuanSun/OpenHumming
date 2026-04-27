import re
from pathlib import Path

from openhumming.skills.creator import SkillCreator, slugify
from openhumming.skills.loader import SkillDocument, load_all_skills, load_skill_file
from openhumming.skills.validator import validate_skill_markdown


class SkillManager:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.creator = SkillCreator(
            Path(__file__).resolve().parent / "templates" / "skill_template.md"
        )

    def list_skills(self) -> list[SkillDocument]:
        return load_all_skills(self.skills_dir)

    def get_skill(self, name_or_slug: str) -> SkillDocument | None:
        target = name_or_slug.strip().lower()
        for skill in self.list_skills():
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
    ) -> SkillDocument:
        content = self.creator.render(
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
        )
        valid, errors = validate_skill_markdown(content)
        if not valid:
            raise ValueError(f"Invalid skill markdown: {', '.join(errors)}")

        slug = slugify(name)
        path = self.skills_dir / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return load_skill_file(path)

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
