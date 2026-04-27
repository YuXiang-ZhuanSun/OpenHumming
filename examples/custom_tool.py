from dataclasses import dataclass

from openhumming.tools.base import Tool, ToolResult


@dataclass
class EchoTool(Tool):
    name: str = "echo"
    description: str = "Return the provided message."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        message = str(input_data.get("message", ""))
        return ToolResult(success=True, content=message)
