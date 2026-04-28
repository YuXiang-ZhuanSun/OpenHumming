from openhumming.agent.state import ReflectionOutcome, TurnObservation, TurnPlan
from openhumming.memory.reflection import MemoryReflectionEngine

SKILL_CREATION_HINTS = (
    "create skill",
    "turn this into a skill",
    "turn this workflow into skill",
    "turn this workflow into a skill",
    "summarize as a skill",
    "next time",
    "\u6c89\u6dc0\u6210",
    "\u56fa\u5316",
    "\u4e0b\u6b21\u4e5f\u8fd9\u4e48\u505a",
)


class Reflection:
    def __init__(self) -> None:
        self.memory_reflection = MemoryReflectionEngine()

    def reflect(
        self,
        message: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> ReflectionOutcome:
        lowered = message.lower()
        return ReflectionOutcome(
            memory_proposals=self.memory_reflection.propose(
                message=message,
                plan=plan,
                observation=observation,
            ),
            should_consider_skill_creation=any(
                hint in lowered for hint in SKILL_CREATION_HINTS
            )
            or (
                bool(observation.tool_results)
                and any(keyword in lowered for keyword in ("workflow", "\u6d41\u7a0b"))
            )
            or (
                plan.intent == "tool_use"
                and len(observation.tool_results) >= 2
                and "repeat" in lowered
            ),
        )
