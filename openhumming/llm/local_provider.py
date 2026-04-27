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
        return (
            "OpenHumming local mode is active.\n\n"
            f"Latest user message: {latest_user_message}\n\n"
            f"I loaded {prior_messages} prior message(s) for context. "
            "Set OPENHUMMING_PROVIDER=openai or anthropic to use a remote model."
        )
