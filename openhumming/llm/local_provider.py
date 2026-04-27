from openhumming.llm.base import ChatMessage, LLMProvider


class LocalProvider(LLMProvider):
    name = "local"

    def generate(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        latest_user_message = next(
            (message.content for message in reversed(messages) if message.role == "user"),
            "",
        )
        prior_messages = max(len(messages) - 1, 0)
        intent = self._extract_section(system_prompt, "## Intent")
        tool_results = self._extract_section(system_prompt, "## Tool Results")
        relevant_skills = self._extract_section(system_prompt, "## Relevant Skills")

        lines = [
            "OpenHumming local mode is active.",
            "",
            f"Latest user message: {latest_user_message}",
            "",
            f"I loaded {prior_messages} prior message(s) for context.",
        ]

        if intent:
            lines.extend(["", f"Detected intent: {intent}"])

        if relevant_skills and relevant_skills != "- No directly matched skills.":
            lines.extend(["", "Relevant skill context:", relevant_skills])

        if tool_results and tool_results != "No tool actions executed.":
            lines.extend(["", "Tool results:", tool_results])

        lines.extend(
            [
                "",
                "Set OPENHUMMING_PROVIDER=openai or anthropic to use a remote model.",
            ]
        )
        return "\n".join(lines)

    def _extract_section(self, system_prompt: str | None, heading: str) -> str:
        if not system_prompt or heading not in system_prompt:
            return ""
        after_heading = system_prompt.split(heading, maxsplit=1)[1].lstrip()
        if "\n## " in after_heading:
            return after_heading.split("\n## ", maxsplit=1)[0].strip()
        return after_heading.strip()
