from dataclasses import dataclass


@dataclass(slots=True)
class MemoryUpdateProposal:
    target: str
    content: str
    reason: str


def is_stable_memory_candidate(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ("prefer", "always", "长期", "偏好", "记住"))
