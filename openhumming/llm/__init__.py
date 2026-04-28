from openhumming.config.settings import Settings
from openhumming.llm.anthropic_provider import AnthropicProvider
from openhumming.llm.base import ChatMessage, LLMProvider
from openhumming.llm.deepseek_provider import DeepSeekProvider
from openhumming.llm.local_provider import LocalProvider
from openhumming.llm.openai_compatible_provider import OpenAICompatibleProvider
from openhumming.llm.openai_provider import OpenAIProvider
from openhumming.llm.provider_settings import ProviderProfile


def build_provider(settings: Settings) -> LLMProvider:
    provider_name = settings.provider.lower()
    if provider_name == "local":
        return LocalProvider()
    if provider_name == "openai":
        return OpenAIProvider(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        )
    if provider_name == "openai_compatible":
        return OpenAICompatibleProvider(
            model=settings.openai_compatible_model,
            api_key=settings.openai_compatible_api_key,
            base_url=settings.openai_compatible_base_url,
            reasoning_effort=settings.openai_compatible_reasoning_effort,
            thinking_enabled=settings.openai_compatible_thinking_enabled,
        )
    if provider_name == "deepseek":
        return DeepSeekProvider(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            reasoning_effort=settings.deepseek_reasoning_effort,
            thinking_enabled=settings.deepseek_thinking_enabled,
        )
    if provider_name == "anthropic":
        return AnthropicProvider(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
        )
    raise ValueError(f"Unsupported provider: {settings.provider}")


def build_provider_from_profile(profile: ProviderProfile) -> LLMProvider:
    provider_name = profile.provider.lower()
    if provider_name == "local":
        return LocalProvider()
    if provider_name == "openai":
        if not profile.model:
            raise ValueError("OpenAI provider requires a model.")
        return OpenAIProvider(
            model=profile.model,
            api_key=profile.api_key,
        )
    if provider_name == "openai_compatible":
        if not profile.model:
            raise ValueError("OpenAI-compatible provider requires a model.")
        return OpenAICompatibleProvider(
            model=profile.model,
            api_key=profile.api_key,
            base_url=profile.base_url,
            reasoning_effort=profile.reasoning_effort,
            thinking_enabled=profile.thinking_enabled,
        )
    if provider_name == "deepseek":
        if not profile.model:
            raise ValueError("DeepSeek provider requires a model.")
        return DeepSeekProvider(
            model=profile.model,
            api_key=profile.api_key,
            base_url=profile.base_url or "https://api.deepseek.com",
            reasoning_effort=profile.reasoning_effort or "high",
            thinking_enabled=True if profile.thinking_enabled is None else profile.thinking_enabled,
        )
    if provider_name == "anthropic":
        if not profile.model:
            raise ValueError("Anthropic provider requires a model.")
        return AnthropicProvider(
            model=profile.model,
            api_key=profile.api_key,
        )
    raise ValueError(f"Unsupported provider: {profile.provider}")


__all__ = ["ChatMessage", "LLMProvider", "build_provider", "build_provider_from_profile"]
