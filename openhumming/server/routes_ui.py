from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from openhumming.server.showcase import load_evolution_showcase


router = APIRouter(include_in_schema=False)
STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/ui")
def ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/showcase/evolution")
def showcase_evolution() -> dict[str, object]:
    return load_evolution_showcase()
