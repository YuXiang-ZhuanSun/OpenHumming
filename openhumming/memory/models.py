from dataclasses import dataclass
from pathlib import Path
from typing import Literal


MemoryTarget = Literal["agent", "user"]
MemoryOperation = Literal["add", "replace", "remove"]


@dataclass(slots=True)
class MemoryUpdateProposal:
    target: MemoryTarget
    section: str
    content: str
    reason: str
    confidence: float = 0.5
    operation: MemoryOperation = "add"
    anchor: str | None = None
    category: str | None = None


@dataclass(slots=True)
class AppliedMemoryUpdate:
    target: MemoryTarget
    section: str
    content: str
    path: Path
    operation: MemoryOperation = "add"
    replaced: str | None = None
