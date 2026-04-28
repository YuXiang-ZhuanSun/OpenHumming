import httpx

from scripts import run_real_demos


def test_demo_server_env_defaults_to_local(monkeypatch) -> None:
    monkeypatch.delenv("OPENHUMMING_PROVIDER", raising=False)
    monkeypatch.delenv(run_real_demos.DEMO_PROVIDER_ENV, raising=False)

    env = run_real_demos._build_demo_server_env(9000)

    assert env["OPENHUMMING_PROVIDER"] == "local"
    assert env["OPENHUMMING_PORT"] == "9000"
    assert env["OPENHUMMING_SCHEDULER_ENABLED"] == "false"


def test_demo_server_env_allows_explicit_provider_override(monkeypatch) -> None:
    monkeypatch.setenv(run_real_demos.DEMO_PROVIDER_ENV, "deepseek")
    monkeypatch.setenv("OPENHUMMING_PROVIDER", "anthropic")

    env = run_real_demos._build_demo_server_env(9001)

    assert env["OPENHUMMING_PROVIDER"] == "deepseek"


def test_decode_response_payload_preserves_non_json_errors() -> None:
    response = httpx.Response(
        500,
        headers={"content-type": "text/plain; charset=utf-8"},
        content=b"provider connection failed",
    )

    payload = run_real_demos._decode_response_payload(response)

    assert payload["error"] == "non_json_response"
    assert payload["status_code"] == 500
    assert payload["content_type"].startswith("text/plain")
    assert "provider connection failed" in payload["body"]
