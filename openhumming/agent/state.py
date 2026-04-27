from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCallPlan:
    tool_name: str
    input_data: dict[str, Any]
    reason: str


@dataclass(slots=True)
class ToolExecutionRecord:
    tool_name: str
    input_data: dict[str, Any]
    success: bool
    content: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TurnPlan:
    intent: str
    relevant_skills: list[str] = field(default_factory=list)
    tool_calls: list[ToolCallPlan] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def needs_tool_execution(self) -> bool:
        return bool(self.tool_calls)


@dataclass(slots=True)
class ExecutionResult:
    actions: list[str] = field(default_factory=list)
    tool_results: list[ToolExecutionRecord] = field(default_factory=list)


@dataclass(slots=True)
class TurnObservation:
    summary: str
    tool_results: list[ToolExecutionRecord] = field(default_factory=list)


@dataclass(slots=True)
class ReflectionOutcome:
    should_update_agent_memory: bool = False
    should_update_user_memory: bool = False
    should_consider_skill_creation: bool = False


@dataclass(slots=True)
class AgentTurnResult:
    session_id: str
    response: str
    actions: list[str]
    memory_updates: dict[str, bool]
