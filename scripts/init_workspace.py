from pathlib import Path

from openhumming.workspace.initializer import initialize_workspace
from openhumming.workspace.paths import WorkspacePaths


def main() -> None:
    paths = WorkspacePaths.from_root(Path("workspace"))
    created = initialize_workspace(paths)
    for item in created:
        print(item)


if __name__ == "__main__":
    main()
