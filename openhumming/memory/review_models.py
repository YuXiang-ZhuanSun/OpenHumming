from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ReviewedSkillDraft:
    name: str
    slug: str
    decision: str
    reason: str
    confidence: float
    source_path: Path
    promoted_path: Path | None = None
