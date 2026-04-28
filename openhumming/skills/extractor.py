import re
from dataclasses import dataclass, field
from typing import Any

from openhumming.skills.workflow_capture import WorkflowCapture

SKILL_NAME_PATTERN = re.compile(
    r"(?:\bskill\b|\u6280\u80fd)\s*[:\uff1a]\s*`?([A-Za-z0-9_\-\u4e00-\u9fff ]+)`?",
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
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillExtractor:
    def draft_from_capture(
        self,
        *,
        capture: WorkflowCapture,
        confidence: float,
        reason: str,
    ) -> SkillDraft:
        name = self._extract_name(capture)
        description = self._build_description(capture)
        when_to_use = self._build_when_to_use(capture)
        inputs = self._build_inputs(capture)
        procedure = self._build_procedure(capture)
        output = self._build_output(capture)
        metadata = {
            "status": "draft",
            "source": "workflow_capture",
            "created_from_sessions": [capture.session_id],
            "confidence": round(confidence, 2),
            "times_reused": 0,
            "capture_reason": reason,
        }
        return SkillDraft(
            name=name,
            description=description,
            when_to_use=when_to_use,
            inputs=inputs,
            procedure=procedure,
            output=output,
            metadata=metadata,
        )

    def _extract_name(self, capture: WorkflowCapture) -> str:
        match = SKILL_NAME_PATTERN.search(capture.user_goal)
        if match:
            return match.group(1).strip()
        if capture.successful_steps:
            tool_names = "_".join(step.tool_name for step in capture.successful_steps[:2])
            return f"{tool_names}_workflow"
        return f"{capture.intent}_workflow"

    def _build_description(self, capture: WorkflowCapture) -> str:
        if capture.successful_steps:
            tools = ", ".join(step.tool_name for step in capture.successful_steps)
            return f"Reusable {capture.intent} workflow using {tools}."
        return f"Reusable workflow for the {capture.intent} intent."

    def _build_when_to_use(self, capture: WorkflowCapture) -> str:
        if capture.intent == "schedule_task":
            return "Use this when the user wants to create or manage a recurring task."
        if capture.intent == "tool_use":
            return "Use this when the user asks for a repeatable workspace operation."
        return "Use this when a completed workflow should be reused later."

    def _build_inputs(self, capture: WorkflowCapture) -> list[str]:
        inputs = ["user goal", "workspace context"]
        normalized_keys = {
            "path": "target path",
            "name": "skill name",
            "slug": "skill slug",
            "natural_language": "schedule request",
            "title": "task title",
            "prompt": "task prompt",
        }
        for step in capture.successful_steps:
            for key in step.input_data:
                label = normalized_keys.get(key)
                if label and label not in inputs:
                    inputs.append(label)
        return inputs

    def _build_procedure(self, capture: WorkflowCapture) -> list[str]:
        procedure: list[str] = ["Understand the user's intended outcome."]
        procedure.extend(capture.plan_notes[:2])
        for step in capture.steps:
            if step.success:
                procedure.append(
                    f"Run `{step.tool_name}` and verify the outcome: {step.outcome_preview or 'success'}."
                )
            else:
                procedure.append(
                    f"Attempt `{step.tool_name}` and surface the failure clearly if it does not succeed."
                )
        if capture.response_summary:
            procedure.append("Summarize the outcome and explain the next useful step.")
        return self._deduplicate(procedure)

    def _build_output(self, capture: WorkflowCapture) -> str:
        if capture.intent == "schedule_task":
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
