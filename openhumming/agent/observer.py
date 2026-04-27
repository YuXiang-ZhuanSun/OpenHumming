from openhumming.agent.state import ExecutionResult, TurnObservation


class Observer:
    def observe(self, execution: ExecutionResult) -> TurnObservation:
        if not execution.tool_results:
            return TurnObservation(
                summary="No tool actions executed.",
                tool_results=[],
            )

        lines: list[str] = []
        for result in execution.tool_results:
            if result.success:
                preview = self._preview(result.content)
                lines.append(f"- {result.tool_name}: success ({preview})")
            else:
                lines.append(f"- {result.tool_name}: failed ({result.error})")
        return TurnObservation(
            summary="\n".join(lines),
            tool_results=execution.tool_results,
        )

    def _preview(self, content: object) -> str:
        if content is None:
            return "no content"
        text = str(content).replace("\n", " ").strip()
        if len(text) <= 120:
            return text
        return text[:117].rstrip() + "..."
