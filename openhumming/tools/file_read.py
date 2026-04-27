from dataclasses import dataclass
from pathlib import Path

from openhumming.tools.base import Tool, ToolResult, resolve_workspace_path


@dataclass
class FileReadTool(Tool):
    root: Path
    name: str = "file_read"
    description: str = "Read a text file from the workspace."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        try:
            path = resolve_workspace_path(self.root, str(input_data["path"]))
            content = path.read_text(encoding="utf-8")
            return ToolResult(success=True, content=content, metadata={"path": str(path)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
