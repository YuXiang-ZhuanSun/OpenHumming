from dataclasses import dataclass, field


@dataclass(slots=True)
class TurnPlan:
    intent: str
    relevant_skills: list[str] = field(default_factory=list)
    needs_tool_execution: bool = False


@dataclass(slots=True)
class ExecutionResult:
    actions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TurnObservation:
    summary: str


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
