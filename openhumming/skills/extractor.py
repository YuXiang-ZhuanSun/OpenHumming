import re
from dataclasses import dataclass

from openhumming.agent.state import TurnObservation, TurnPlan

SKILL_CREATION_HINTS = (
    "create skill",
    "turn this into a skill",
    "summarize as a skill",
    "\u6c89\u6dc0\u6210",
    "\u56fa\u5316",
    "\u603b\u7ed3\u6210 skill",
)
SKILL_NAME_PATTERN = re.compile(
    r"(?:skill|技能)\s*[:：]\s*`?([A-Za-z0-9_\-\u4e00-\u9fff ]+)`?",
    re.IGNORECASE,
)


@dataclass(slots=True)
class SkillDraft:
    name: str
    description: str
    when_to_use: str
    inputs: list[str]
    procedure: list[str]
    output: str


class SkillExtractor:
    def should_create_skill(
        self,
        message: str,
        observation: TurnObservation,
    ) -> bool:
        lowered = message.lower()
        explicit_hint = any(hint in lowered for hint in SKILL_CREATION_HINTS)
        reuse_hint = any(
            hint in lowered
            for hint in ("next time", "\u4e0b\u6b21\u4e5f\u8fd9\u4e48\u505a")
        )
        return explicit_hint or (reuse_hint and bool(observation.tool_results))

    def draft_from_turn(
        self,
        *,
        message: str,
        response: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> SkillDraft | None:
        if not self.should_create_skill(message, observation):
            return None

        name = self._extract_name(message, plan, observation)
        description = self._build_description(plan, observation)
        when_to_use = self._build_when_to_use(plan)
        inputs = self._build_inputs(observation)
        procedure = self._build_procedure(plan, observation, response)
        output = self._build_output(plan)

        return SkillDraft(
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
        )

    def _extract_name(
        self,
        message: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> str:
        match = SKILL_NAME_PATTERN.search(message)
        if match:
            return match.group(1).strip()

        if observation.tool_results:
            tool_names = "_".join(result.tool_name for result in observation.tool_results[:2])
            return f"{tool_names}_workflow"
        return f"{plan.intent}_workflow"

    def _build_description(
        self,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> str:
        if observation.tool_results:
            tools = ", ".join(result.tool_name for result in observation.tool_results)
            return f"Reusable {plan.intent} workflow using {tools}."
        return f"Reusable workflow for the {plan.intent} intent."

    def _build_when_to_use(self, plan: TurnPlan) -> str:
        if plan.intent == "schedule_task":
            return "Use this when the user wants to create or manage a recurring task."
        if plan.intent == "tool_use":
            return "Use this when the user asks for a workspace operation that should be repeatable."
        return "Use this when a completed workflow should be reused later."

    def _build_inputs(self, observation: TurnObservation) -> list[str]:
        inputs = ["user goal", "workspace context"]
        for result in observation.tool_results:
            path = result.input_data.get("path")
            if path and "target path" not in inputs:
                inputs.append("target path")
            natural_language = result.input_data.get("natural_language")
            if natural_language and "schedule request" not in inputs:
                inputs.append("schedule request")
        return inputs

    def _build_procedure(
        self,
        plan: TurnPlan,
        observation: TurnObservation,
        response: str,
    ) -> list[str]:
        procedure: list[str] = ["Understand the user's intended outcome."]
        procedure.extend(plan.notes[:2])

        for result in observation.tool_results:
            if result.success:
                procedure.append(
                    f"Run `{result.tool_name}` with the required inputs and verify the result."
                )
            else:
                procedure.append(
                    f"Attempt `{result.tool_name}` and surface the failure clearly if it does not succeed."
                )

        if response.strip():
            procedure.append("Summarize the outcome and explain the next useful step.")
        return self._deduplicate(procedure)

    def _build_output(self, plan: TurnPlan) -> str:
        if plan.intent == "schedule_task":
            return "A created task definition and a concise explanation of the schedule."
        return "A completed workflow result plus a concise explanation of what was done."

    def _deduplicate(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            normalized = item.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique
