from dataclasses import dataclass
from pathlib import Path

from openhumming.tools.base import Tool, ToolResult, resolve_workspace_path


@dataclass
class ListDirTool(Tool):
    root: Path
    name: str = "list_dir"
    description: str = "List files and directories inside the workspace."

    def run(self, input_data: dict[str, object]) -> ToolResult:
        try:
            path = resolve_workspace_path(self.root, str(input_data.get("path", ".")))
            items = [
                {
                    "name": item.name,
                    "is_dir": item.is_dir(),
                }
                for item in sorted(path.iterdir())
            ]
            return ToolResult(success=True, content=items, metadata={"path": str(path)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
