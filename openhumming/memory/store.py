from dataclasses import dataclass
from typing import Any

from openhumming.memory.conversation import ConversationStore, StoredMessage
from openhumming.memory.profile import load_profiles
from openhumming.workspace.paths import WorkspacePaths


@dataclass(slots=True)
class MemoryContext:
    agent_profile: str
    user_profile: str
    conversation_history: list[StoredMessage]


class MemoryStore:
    def __init__(self, paths: WorkspacePaths) -> None:
        self.paths = paths
        self.conversations = ConversationStore(paths)

    def load_context(
        self,
        history_limit: int = 20,
        session_id: str | None = None,
    ) -> MemoryContext:
        profiles = load_profiles(self.paths)
        history = self.conversations.recent_messages(
            limit=history_limit,
            session_id=session_id,
        )
        return MemoryContext(
            agent_profile=profiles.agent_profile,
            user_profile=profiles.user_profile,
            conversation_history=history,
        )

    def save_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.conversations.append_turn(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            metadata=metadata,
        )
