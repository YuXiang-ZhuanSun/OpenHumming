import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openhumming.workspace.paths import WorkspacePaths


@dataclass(slots=True)
class StoredMessage:
    role: str
    content: str
    timestamp: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationStore:
    def __init__(self, paths: WorkspacePaths) -> None:
        self.paths = paths

    def append_message(
        self,
        role: str,
        content: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "metadata": metadata or {},
        }
        destination = self.paths.conversation_file()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def append_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        turn_metadata = metadata or {}
        self.append_message("user", user_message, session_id, turn_metadata)
        self.append_message("assistant", assistant_message, session_id, turn_metadata)

    def recent_messages(
        self,
        limit: int = 20,
        session_id: str | None = None,
    ) -> list[StoredMessage]:
        if limit <= 0:
            return []
        records: list[StoredMessage] = []
        for file_path in self._conversation_files():
            records.extend(self._read_messages_from_file(file_path, session_id=session_id))
        return records[-limit:]

    def messages_for_date(
        self,
        target_date,
        session_id: str | None = None,
    ) -> list[StoredMessage]:
        file_path = self.paths.conversation_file(target_date)
        if not file_path.exists():
            return []
        return self._read_messages_from_file(file_path, session_id=session_id)

    def _conversation_files(self) -> list[Path]:
        if not self.paths.conversations_dir.exists():
            return []
        return sorted(self.paths.conversations_dir.glob("*.jsonl"))

    def _read_messages_from_file(
        self,
        file_path: Path,
        session_id: str | None = None,
    ) -> list[StoredMessage]:
        records: list[StoredMessage] = []
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            if session_id and raw.get("session_id") != session_id:
                continue
            records.append(
                StoredMessage(
                    role=raw["role"],
                    content=raw["content"],
                    timestamp=raw["timestamp"],
                    session_id=raw["session_id"],
                    metadata=raw.get("metadata", {}),
                )
            )
        return records
