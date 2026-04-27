from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        raise NotImplementedError
