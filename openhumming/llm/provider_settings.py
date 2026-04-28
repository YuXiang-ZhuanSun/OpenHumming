from copy import deepcopy
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from openhumming.config.settings import Settings

SUPPORTED_PROVIDER_IDS = (
    "local",
    "openai",
    "openai_compatible",
    "deepseek",
    "anthropic",
)
DEFAULT_OPENAI_COMPATIBLE_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    id: str
    label: str
    description: str


PROVIDER_DESCRIPTORS = (
    ProviderDescriptor(
        id="local",
        label="Local",
        description="Offline local placeholder provider for deterministic demos and development.",
    ),
    ProviderDescriptor(
        id="openai",
        label="OpenAI",
        description="Official OpenAI Responses API provider.",
    ),
    ProviderDescriptor(
        id="openai_compatible",
        label="OpenAI-Compatible",
        description="Any API that exposes an OpenAI-compatible chat completions endpoint.",
    ),
    ProviderDescriptor(
        id="deepseek",
        label="DeepSeek",
        description="DeepSeek chat completions provider with optional reasoning controls.",
    ),
    ProviderDescriptor(
        id="anthropic",
        label="Anthropic",
        description="Official Anthropic Messages API provider.",
    ),
)


@dataclass(slots=True)
class ProviderProfile:
    provider: str
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None
    thinking_enabled: bool | None = None

    def to_public_payload(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "reasoning_effort": self.reasoning_effort,
            "thinking_enabled": self.thinking_enabled,
            "has_api_key": bool(self.api_key),
        }


@dataclass(slots=True)
class ProviderSettingsDocument:
    active_provider: str
    profiles: dict[str, ProviderProfile]

    @property
    def active_profile(self) -> ProviderProfile:
        return self.profiles[self.active_provider]


def build_default_provider_settings(settings: Settings) -> ProviderSettingsDocument:
    provider = settings.provider.strip().lower()
    if provider not in SUPPORTED_PROVIDER_IDS:
        provider = "local"
    profiles = {
        "local": ProviderProfile(provider="local"),
        "openai": ProviderProfile(
            provider="openai",
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        ),
        "openai_compatible": ProviderProfile(
            provider="openai_compatible",
            model=settings.openai_compatible_model,
            api_key=settings.openai_compatible_api_key,
            base_url=settings.openai_compatible_base_url,
            reasoning_effort=settings.openai_compatible_reasoning_effort,
            thinking_enabled=settings.openai_compatible_thinking_enabled,
        ),
        "deepseek": ProviderProfile(
            provider="deepseek",
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            reasoning_effort=settings.deepseek_reasoning_effort,
            thinking_enabled=settings.deepseek_thinking_enabled,
        ),
        "anthropic": ProviderProfile(
            provider="anthropic",
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
        ),
    }
    return ProviderSettingsDocument(active_provider=provider, profiles=profiles)


class ProviderSettingsStore:
    def __init__(self, path: Path, settings: Settings) -> None:
        self.path = path
        self.settings = settings

    def load(self) -> ProviderSettingsDocument:
        raw = self._load_raw_payload()
        return self._build_document_from_raw_payload(raw)

    def update_profile(
        self,
        *,
        provider: str,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        clear_api_key: bool = False,
        reasoning_effort: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> ProviderSettingsDocument:
        raw, document = self.preview_update(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            clear_api_key=clear_api_key,
            reasoning_effort=reasoning_effort,
            thinking_enabled=thinking_enabled,
        )
        self._write_raw_payload(raw)
        return document

    def preview_update(
        self,
        *,
        provider: str,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        clear_api_key: bool = False,
        reasoning_effort: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> tuple[dict[str, Any], ProviderSettingsDocument]:
        provider_id = provider.strip().lower()
        if provider_id not in SUPPORTED_PROVIDER_IDS:
            raise ValueError(f"Unsupported provider: {provider}")

        raw = deepcopy(self._load_raw_payload())
        raw["active_provider"] = provider_id
        raw_profiles = raw.setdefault("profiles", {})
        if not isinstance(raw_profiles, dict):
            raw_profiles = {}
            raw["profiles"] = raw_profiles
        profile_payload = raw_profiles.setdefault(provider_id, {})
        if not isinstance(profile_payload, dict):
            profile_payload = {}
            raw_profiles[provider_id] = profile_payload

        for field_name, value in (
            ("model", model),
            ("base_url", base_url),
            ("reasoning_effort", reasoning_effort),
        ):
            if value is not None:
                profile_payload[field_name] = self._normalize_text(value)

        if thinking_enabled is not None:
            profile_payload["thinking_enabled"] = bool(thinking_enabled)

        if clear_api_key:
            profile_payload["api_key"] = None
        elif api_key is not None:
            profile_payload["api_key"] = self._normalize_text(api_key)

        return raw, self._build_document_from_raw_payload(raw)

    def _load_raw_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _write_raw_payload(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def save_preview(self, payload: dict[str, Any]) -> None:
        self._write_raw_payload(payload)

    def _build_document_from_raw_payload(
        self,
        raw: dict[str, Any],
    ) -> ProviderSettingsDocument:
        defaults = build_default_provider_settings(self.settings)
        raw_profiles = raw.get("profiles", {})
        if not isinstance(raw_profiles, dict):
            raw_profiles = {}

        active_provider = str(raw.get("active_provider") or defaults.active_provider).strip().lower()
        if active_provider not in SUPPORTED_PROVIDER_IDS:
            active_provider = defaults.active_provider

        profiles: dict[str, ProviderProfile] = {}
        for provider_id, base_profile in defaults.profiles.items():
            override = raw_profiles.get(provider_id, {})
            profiles[provider_id] = self._merge_profile(base_profile, override)

        return ProviderSettingsDocument(
            active_provider=active_provider,
            profiles=profiles,
        )

    def _merge_profile(
        self,
        base_profile: ProviderProfile,
        override: object,
    ) -> ProviderProfile:
        profile = replace(base_profile)
        if not isinstance(override, dict):
            return profile

        for field_name in (
            "model",
            "api_key",
            "base_url",
            "reasoning_effort",
            "thinking_enabled",
        ):
            if field_name not in override:
                continue
            value = override[field_name]
            if field_name == "thinking_enabled":
                setattr(profile, field_name, None if value is None else bool(value))
                continue
            setattr(profile, field_name, self._normalize_text(value))
        return profile

    def _normalize_text(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
