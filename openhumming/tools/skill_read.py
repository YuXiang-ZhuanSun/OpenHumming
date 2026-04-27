from dataclasses import dataclass

from openhumming.skills.manager import SkillManager
from openhumming.tools.base import Tool, ToolResult


@dataclass
class SkillReadTool(Tool):
    skill_manager: SkillManager
    name: str = "skill_read"
    description: str = "Read a skill markdown document by name or slug."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        target = str(input_data.get("name") or input_data.get("slug") or "")
        skill = self.skill_manager.get_skill(target)
        if skill is None:
            return ToolResult(success=False, error=f"Unknown skill: {target}")
        return ToolResult(
            success=True,
            content=skill.content,
            metadata={"name": skill.name, "path": str(skill.path)},
        )
