from openhumming.llm.base import ChatMessage, LLMProvider


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com",
        reasoning_effort: str = "high",
        thinking_enabled: bool = True,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
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
                "DeepSeek provider requires the 'openai' package. "
                "Install with 'pip install .[providers]'."
            ) from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        request_messages: list[dict[str, str]] = []
        if system_prompt:
            request_messages.append({"role": "system", "content": system_prompt})
        request_messages.extend(
            {"role": message.role, "content": message.content}
            for message in messages
        )

        extra_body = {"thinking": {"type": "enabled"}} if self.thinking_enabled else None
        response = client.chat.completions.create(
            model=self.model,
            messages=request_messages,
            stream=False,
            reasoning_effort=self.reasoning_effort,
            extra_body=extra_body,
        )
        message = response.choices[0].message
        return (message.content or "").strip()
