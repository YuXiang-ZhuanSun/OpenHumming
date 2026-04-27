from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ToolResult:
    success: bool
    content: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> ToolResult:
        raise NotImplementedError


def resolve_workspace_path(root: Path, requested_path: str) -> Path:
    candidate = (root / requested_path).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"Path is outside the workspace: {requested_path}")
    return candidate
