from dataclasses import dataclass
from pathlib import Path

from openhumming.tools.base import Tool, ToolResult, resolve_workspace_path


@dataclass
class FileWriteTool(Tool):
    root: Path
    name: str = "file_write"
    description: str = "Write text to a file in the workspace."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        try:
            path = resolve_workspace_path(self.root, str(input_data["path"]))
            content = str(input_data.get("content", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=str(path), metadata={"path": str(path)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
