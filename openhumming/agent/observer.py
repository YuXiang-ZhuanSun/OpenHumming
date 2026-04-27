from openhumming.agent.state import ExecutionResult, TurnObservation


class Observer:
    def observe(self, execution: ExecutionResult) -> TurnObservation:
        return TurnObservation(
            summary=f"Executed {len(execution.actions)} tool action(s)."
        )
