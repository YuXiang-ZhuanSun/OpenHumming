from dataclasses import dataclass
from pathlib import Path

from openhumming.workspace.paths import WorkspacePaths


@dataclass(slots=True)
class ProfileSnapshot:
    agent_profile: str
    user_profile: str


def read_markdown_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_profiles(paths: WorkspacePaths) -> ProfileSnapshot:
    return ProfileSnapshot(
        agent_profile=read_markdown_file(paths.agent_profile),
        user_profile=read_markdown_file(paths.user_profile),
    )
