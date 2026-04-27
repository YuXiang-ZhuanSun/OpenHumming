from openhumming.llm.base import ChatMessage, LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def generate(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI provider requires the 'openai' package. "
                "Install with 'pip install .[providers]'."
            ) from exc

        client = OpenAI(api_key=self.api_key)
        input_messages: list[dict[str, object]] = []
        if system_prompt:
            input_messages.append(
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                }
            )
        for message in messages:
            input_messages.append(
                {
                    "role": message.role,
                    "content": [{"type": "input_text", "text": message.content}],
                }
            )
        response = client.responses.create(model=self.model, input=input_messages)
        output_text = getattr(response, "output_text", "")
        return output_text.strip() or str(response)
