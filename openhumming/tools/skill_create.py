from dataclasses import dataclass

from openhumming.skills.manager import SkillManager
from openhumming.tools.base import Tool, ToolResult


@dataclass
class SkillCreateTool(Tool):
    skill_manager: SkillManager
    name: str = "skill_create"
    description: str = "Create a new markdown skill."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        try:
            skill = self.skill_manager.create_skill(
                name=str(input_data["name"]),
                description=str(input_data.get("description", "")),
                when_to_use=str(input_data.get("when_to_use", "")),
                inputs=[str(item) for item in input_data.get("inputs", [])],
                procedure=[str(item) for item in input_data.get("procedure", [])],
                output=str(input_data.get("output", "")),
            )
            return ToolResult(
                success=True,
                content=skill.content,
                metadata={"name": skill.name, "path": str(skill.path)},
            )
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
