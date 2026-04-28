from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from openhumming.llm import build_provider_from_profile
from openhumming.llm.provider_settings import PROVIDER_DESCRIPTORS, ProviderSettingsDocument


router = APIRouter(tags=["settings"])


class ProviderOptionResponse(BaseModel):
    id: str
    label: str
    description: str


class ProviderProfileResponse(BaseModel):
    provider: str
    model: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None
    thinking_enabled: bool | None = None
    has_api_key: bool


class ProviderSettingsResponse(BaseModel):
    active_provider: str
    config_path: str
    available_providers: list[ProviderOptionResponse]
    profiles: dict[str, ProviderProfileResponse]


class ProviderSettingsUpdateRequest(BaseModel):
    active_provider: str = Field(min_length=1)
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    clear_api_key: bool = False
    reasoning_effort: str | None = None
    thinking_enabled: bool | None = None

    @field_validator(
        "active_provider",
        "model",
        "base_url",
        "api_key",
        "reasoning_effort",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


@router.get("/settings/provider", response_model=ProviderSettingsResponse)
def get_provider_settings(request: Request) -> ProviderSettingsResponse:
    document = request.app.state.provider_settings_store.load()
    return _build_response(document, request)


@router.post("/settings/provider", response_model=ProviderSettingsResponse)
def update_provider_settings(
    payload: ProviderSettingsUpdateRequest,
    request: Request,
) -> ProviderSettingsResponse:
    store = request.app.state.provider_settings_store
    try:
        raw_payload, document = store.preview_update(
            provider=payload.active_provider,
            model=payload.model,
            base_url=payload.base_url,
            api_key=payload.api_key,
            clear_api_key=payload.clear_api_key,
            reasoning_effort=payload.reasoning_effort,
            thinking_enabled=payload.thinking_enabled,
        )
        provider = build_provider_from_profile(document.active_profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.save_preview(raw_payload)
    request.app.state.runtime.provider = provider
    request.app.state.trace_recorder.record(
        "provider_settings_updated",
        {
            "provider": document.active_provider,
            "config_path": str(request.app.state.paths.provider_settings_file),
        },
    )
    return _build_response(document, request)


def _build_response(
    document: ProviderSettingsDocument,
    request: Request,
) -> ProviderSettingsResponse:
    return ProviderSettingsResponse(
        active_provider=document.active_provider,
        config_path=str(request.app.state.paths.provider_settings_file),
        available_providers=[
            ProviderOptionResponse(
                id=item.id,
                label=item.label,
                description=item.description,
            )
            for item in PROVIDER_DESCRIPTORS
        ],
        profiles={
            provider_id: ProviderProfileResponse(**profile.to_public_payload())
            for provider_id, profile in document.profiles.items()
        },
    )
