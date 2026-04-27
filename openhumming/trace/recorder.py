import json
from typing import Any

from openhumming.trace.events import TraceEvent
from openhumming.workspace.paths import WorkspacePaths


class TraceRecorder:
    def __init__(self, paths: WorkspacePaths) -> None:
        self.paths = paths

    def record(self, event: str, payload: dict[str, Any]) -> TraceEvent:
        trace_event = TraceEvent(event=event, payload=payload)
        destination = self.paths.trace_file()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace_event.as_dict(), ensure_ascii=False) + "\n")
        return trace_event
