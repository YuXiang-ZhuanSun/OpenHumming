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
        lowered = user_message.lower()
        matched = [
            skill
            for skill in self.list_skills()
            if skill.slug.lower() in lowered or skill.name.lower() in lowered
        ]
        return matched[:limit]

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
