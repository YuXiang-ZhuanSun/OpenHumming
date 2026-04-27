import pytest

from openhumming.config.settings import Settings
from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths


@pytest.fixture
def workspace_paths(tmp_path):
    paths = WorkspacePaths.from_root(tmp_path / "workspace")
    initialize_workspace(paths)
    return paths


@pytest.fixture
def settings(workspace_paths):
    return Settings(
        workspace_root=workspace_paths.root,
        provider="local",
        conversation_history_limit=10,
    )
