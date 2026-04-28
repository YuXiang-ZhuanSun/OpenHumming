from dataclasses import dataclass, field

from openhumming.agent.state import TurnObservation, TurnPlan


@dataclass(slots=True)
class WorkflowStep:
    tool_name: str
    reason: str
    input_data: dict[str, object]
    success: bool
    outcome_preview: str
    error: str | None = None


@dataclass(slots=True)
class WorkflowCapture:
    session_id: str
    user_goal: str
    intent: str
    plan_notes: list[str] = field(default_factory=list)
    steps: list[WorkflowStep] = field(default_factory=list)
    response_summary: str = ""
    completed: bool = False

    @property
    def successful_steps(self) -> list[WorkflowStep]:
        return [step for step in self.steps if step.success]

    @property
    def input_keys(self) -> set[str]:
        keys: set[str] = set()
        for step in self.steps:
            keys.update(step.input_data.keys())
        return keys


class WorkflowCaptureBuilder:
    def capture(
        self,
        *,
        session_id: str,
        message: str,
        response: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> WorkflowCapture:
        steps = [
            WorkflowStep(
                tool_name=result.tool_name,
                reason=self._reason_for_tool(plan, result.tool_name),
                input_data={key: value for key, value in result.input_data.items()},
                success=result.success,
                outcome_preview=self._preview(result.content),
                error=result.error,
            )
            for result in observation.tool_results
        ]
        return WorkflowCapture(
            session_id=session_id,
            user_goal=message,
            intent=plan.intent,
            plan_notes=list(plan.notes),
            steps=steps,
            response_summary=self._preview(response, limit=200),
            completed=bool(steps) and any(step.success for step in steps),
        )

    def _reason_for_tool(self, plan: TurnPlan, tool_name: str) -> str:
        for tool_call in plan.tool_calls:
            if tool_call.tool_name == tool_name:
                return tool_call.reason
        return "Tool was selected during workflow execution."

    def _preview(self, value: object, limit: int = 120) -> str:
        text = str(value or "").replace("\n", " ").strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."
