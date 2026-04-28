import json
import re
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", value.strip().lower())
    return normalized.strip("_") or "skill"


class SkillCreator:
    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path

    def render(
        self,
        *,
        name: str,
        description: str,
        when_to_use: str,
        inputs: list[str],
        procedure: list[str],
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        rendered_inputs = "\n".join(f"- {item}" for item in inputs) or "- None"
        rendered_procedure = "\n".join(
            f"{index}. {step}" for index, step in enumerate(procedure, start=1)
        ) or "1. Execute the workflow."
        content = template.format(
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=rendered_inputs,
            procedure=rendered_procedure,
            output=output,
        ).strip()
        if metadata:
            content = self.render_frontmatter(metadata) + "\n" + content
        return content.rstrip() + "\n"

    def render_frontmatter(self, metadata: dict[str, Any]) -> str:
        lines = ["---"]
        for key, value in metadata.items():
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        lines.append("---")
        return "\n".join(lines)
