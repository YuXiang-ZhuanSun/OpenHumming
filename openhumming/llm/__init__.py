from openhumming.config.settings import Settings
from openhumming.llm.anthropic_provider import AnthropicProvider
from openhumming.llm.base import ChatMessage, LLMProvider
from openhumming.llm.local_provider import LocalProvider
from openhumming.llm.openai_provider import OpenAIProvider


def build_provider(settings: Settings) -> LLMProvider:
    provider_name = settings.provider.lower()
    if provider_name == "local":
        return LocalProvider()
    if provider_name == "openai":
        return OpenAIProvider(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        )
    if provider_name == "anthropic":
        return AnthropicProvider(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
        )
    raise ValueError(f"Unsupported provider: {settings.provider}")


__all__ = ["ChatMessage", "LLMProvider", "build_provider"]
