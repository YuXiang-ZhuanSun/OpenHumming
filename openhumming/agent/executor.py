from openhumming.agent.state import ExecutionResult, TurnPlan
from openhumming.tools.registry import ToolRegistry


class Executor:
    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        self.tool_registry = tool_registry

    def execute(self, plan: TurnPlan) -> ExecutionResult:
        _ = plan
        return ExecutionResult(actions=[])
