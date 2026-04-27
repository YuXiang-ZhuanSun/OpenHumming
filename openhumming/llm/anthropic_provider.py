from openhumming.llm.base import ChatMessage, LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def generate(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Anthropic provider requires the 'anthropic' package. "
                "Install with 'pip install .[providers]'."
            ) from exc

        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=800,
            system=system_prompt or "",
            messages=[
                {"role": message.role, "content": message.content}
                for message in messages
                if message.role in {"user", "assistant"}
            ],
        )
        for block in response.content:
            if getattr(block, "type", "") == "text":
                return getattr(block, "text", "").strip()
        return str(response)
