from openhumming.agent.state import ExecutionResult, ToolExecutionRecord, TurnPlan
from openhumming.tools.registry import ToolRegistry
from openhumming.trace.recorder import TraceRecorder


class Executor:
    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        trace_recorder: TraceRecorder | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.trace_recorder = trace_recorder

    def execute(self, plan: TurnPlan) -> ExecutionResult:
        if self.tool_registry is None or not plan.tool_calls:
            return ExecutionResult(actions=[], tool_results=[])

        actions: list[str] = []
        tool_results: list[ToolExecutionRecord] = []
        for tool_call in plan.tool_calls:
            result = self.tool_registry.execute(tool_call.tool_name, tool_call.input_data)
            record = ToolExecutionRecord(
                tool_name=tool_call.tool_name,
                input_data=tool_call.input_data,
                success=result.success,
                content=result.content,
                error=result.error,
                metadata=result.metadata,
            )
            tool_results.append(record)
            actions.append(f"tool:{tool_call.tool_name}")
            if self.trace_recorder is not None:
                self.trace_recorder.record(
                    "tool_call",
                    {
                        "tool": tool_call.tool_name,
                        "input": tool_call.input_data,
                        "success": result.success,
                        "error": result.error,
                    },
                )

        return ExecutionResult(actions=actions, tool_results=tool_results)
