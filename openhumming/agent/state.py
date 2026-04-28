from dataclasses import dataclass, field
from typing import Any

from openhumming.memory.models import AppliedMemoryUpdate, MemoryUpdateProposal


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
    memory_proposals: list[MemoryUpdateProposal] = field(default_factory=list)
    should_consider_skill_creation: bool = False

    @property
    def should_update_agent_memory(self) -> bool:
        return any(proposal.target == "agent" for proposal in self.memory_proposals)

    @property
    def should_update_user_memory(self) -> bool:
        return any(proposal.target == "user" for proposal in self.memory_proposals)


@dataclass(slots=True)
class AgentTurnResult:
    session_id: str
    response: str
    actions: list[str]
    memory_updates: dict[str, bool]
    memory_proposals: list[MemoryUpdateProposal] = field(default_factory=list)
    applied_memory_updates: list[AppliedMemoryUpdate] = field(default_factory=list)
    created_skill_draft: dict[str, Any] | None = None
