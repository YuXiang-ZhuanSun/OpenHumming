import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SkillDocument:
    name: str
    slug: str
    description: str
    content: str
    path: Path
    status: str = "published"
    metadata: dict[str, Any] = field(default_factory=dict)


def load_skill_file(path: Path) -> SkillDocument:
    content = path.read_text(encoding="utf-8").strip()
    metadata, body = _split_frontmatter(content)
    lines = body.splitlines()
    title = path.stem.replace("_", " ").title()
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("# ").replace("Skill: ", "").strip()

    description = ""
    marker = "## Description"
    if marker in body:
        after_marker = body.split(marker, maxsplit=1)[1].strip()
        description = after_marker.split("\n## ", maxsplit=1)[0].strip()

    status = str(metadata.get("status") or _infer_status(path))
    return SkillDocument(
        name=title,
        slug=path.stem,
        description=description,
        content=content,
        path=path,
        status=status,
        metadata=metadata,
    )


def load_all_skills(
    skills_dir: Path,
    *,
    exclude_dir_names: set[str] | None = None,
) -> list[SkillDocument]:
    if not skills_dir.exists():
        return []
    excluded = {item.lower() for item in (exclude_dir_names or set())}
    skill_files = sorted(
        path
        for path in skills_dir.rglob("*.md")
        if path.name.lower() != "readme.md"
        and not _path_contains_excluded_dir(path, skills_dir, excluded)
    )
    return [load_skill_file(path) for path in skill_files]


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content
    closing_index = content.find("\n---\n", 4)
    if closing_index < 0:
        return {}, content
    raw_frontmatter = content[4:closing_index]
    body = content[closing_index + 5 :]
    metadata: dict[str, Any] = {}
    for line in raw_frontmatter.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw_value = line.split(":", maxsplit=1)
        metadata[key.strip()] = _parse_frontmatter_value(raw_value.strip())
    return metadata, body.strip()


def _parse_frontmatter_value(raw_value: str) -> Any:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value.strip().strip('"')


def _infer_status(path: Path) -> str:
    return "draft" if path.parent.name.lower() == "drafts" else "published"


def _path_contains_excluded_dir(
    path: Path,
    root: Path,
    excluded: set[str],
) -> bool:
    if not excluded:
        return False
    relative_parts = path.relative_to(root).parts[:-1]
    return any(part.lower() in excluded for part in relative_parts)
