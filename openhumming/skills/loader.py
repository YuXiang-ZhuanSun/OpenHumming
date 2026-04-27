from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SkillDocument:
    name: str
    slug: str
    description: str
    content: str
    path: Path


def load_skill_file(path: Path) -> SkillDocument:
    content = path.read_text(encoding="utf-8").strip()
    lines = content.splitlines()
    title = path.stem.replace("_", " ").title()
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("# ").replace("Skill: ", "").strip()

    description = ""
    marker = "## Description"
    if marker in content:
        after_marker = content.split(marker, maxsplit=1)[1].strip()
        description = after_marker.split("\n## ", maxsplit=1)[0].strip()

    return SkillDocument(
        name=title,
        slug=path.stem,
        description=description,
        content=content,
        path=path,
    )


def load_all_skills(skills_dir: Path) -> list[SkillDocument]:
    if not skills_dir.exists():
        return []
    skill_files = sorted(
        path for path in skills_dir.glob("*.md") if path.name.lower() != "readme.md"
    )
    return [load_skill_file(path) for path in skill_files]
