from dataclasses import dataclass

from openhumming.scheduler.manager import TaskManager
from openhumming.tools.base import Tool, ToolResult


@dataclass
class TaskCreateTool(Tool):
    task_manager: TaskManager
    name: str = "task_create"
    description: str = "Create a scheduled task from natural-language input."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        try:
            task = self.task_manager.create_from_text(
                natural_language=str(input_data["natural_language"]),
                prompt=str(input_data.get("prompt", "")) or None,
                title=str(input_data.get("title", "")) or None,
            )
            return ToolResult(success=True, content=task.prompt, metadata={"id": task.id})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
