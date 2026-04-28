from openhumming.llm.base import ChatMessage, LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    name = "openai_compatible"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        reasoning_effort: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else None
        self.reasoning_effort = reasoning_effort
        self.thinking_enabled = thinking_enabled

    def generate(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI-compatible providers require the 'openai' package. "
                "Install with 'pip install .[providers]'."
            ) from exc

        client_kwargs: dict[str, object] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = OpenAI(**client_kwargs)

        request_messages: list[dict[str, str]] = []
        if system_prompt:
            request_messages.append({"role": "system", "content": system_prompt})
        request_messages.extend(
            {"role": message.role, "content": message.content}
            for message in messages
        )

        request_kwargs: dict[str, object] = {
            "model": self.model,
            "messages": request_messages,
            "stream": False,
        }
        if self.reasoning_effort:
            request_kwargs["reasoning_effort"] = self.reasoning_effort
        if self.thinking_enabled:
            request_kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

        response = client.chat.completions.create(**request_kwargs)
        message = response.choices[0].message
        return (message.content or "").strip()
