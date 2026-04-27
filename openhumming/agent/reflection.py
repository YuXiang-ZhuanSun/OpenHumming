from openhumming.agent.state import ReflectionOutcome, TurnObservation, TurnPlan

USER_MEMORY_HINTS = (
    "remember",
    "i prefer",
    "my preference",
    "\u8bb0\u4f4f",
    "\u504f\u597d",
    "\u6211\u559c\u6b22",
    "\u6211\u66f4\u559c\u6b22",
)
SKILL_CREATION_HINTS = (
    "create skill",
    "turn this into a skill",
    "summarize as a skill",
    "next time",
    "\u6c89\u6dc0\u6210",
    "\u56fa\u5316",
    "\u4e0b\u6b21\u4e5f\u8fd9\u4e48\u505a",
)


class Reflection:
    def reflect(
        self,
        message: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> ReflectionOutcome:
        lowered = message.lower()
        return ReflectionOutcome(
            should_update_agent_memory=False,
            should_update_user_memory=any(
                hint in lowered for hint in USER_MEMORY_HINTS
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
