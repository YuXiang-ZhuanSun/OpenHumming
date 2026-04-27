from openhumming.agent.state import ReflectionOutcome, TurnObservation, TurnPlan


class Reflection:
    def reflect(
        self,
        message: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> ReflectionOutcome:
        lowered = message.lower()
        _ = observation
        return ReflectionOutcome(
            should_update_agent_memory=False,
            should_update_user_memory=any(
                keyword in lowered for keyword in ("remember", "记住", "偏好", "prefer")
            ),
            should_consider_skill_creation=plan.intent == "skill_work"
            or any(keyword in message for keyword in ("下次也这么做", "沉淀成", "固化")),
        )
