from fastapi.testclient import TestClient

from openhumming.server.app import create_app
from openhumming.skills.manager import SkillManager


def test_chat_endpoint_persists_conversation(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))

    response = client.post(
        "/chat",
        json={"message": "hello from api", "session_id": "session-api"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "session-api"
    assert "hello from api" in payload["response"]
    assert "record_conversation" in payload["actions"]
    assert "memory_proposals" in payload
    assert "applied_memory_updates" in payload
    assert "created_skill_draft" in payload

    memory_response = client.get("/memory/agent")
    assert memory_response.status_code == 200
    assert "OpenHumming" in memory_response.json()["content"]

    conversation_file = workspace_paths.conversation_file()
    assert conversation_file.exists()


def test_ui_route_and_showcase_endpoint(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))

    ui_response = client.get("/ui")
    showcase_response = client.get("/showcase/evolution")

    assert ui_response.status_code == 200
    assert "OpenHumming Local Console" in ui_response.text
    assert showcase_response.status_code == 200
    payload = showcase_response.json()
    assert payload["items"]
    assert payload["items"][0]["label"]["zh"]


def test_daily_review_endpoint_runs_review(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))
    client.post(
        "/chat",
        json={"message": "Remember that I prefer local-first workflows", "session_id": "session-review"},
    )

    response = client.post("/reviews/daily")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary_path"].endswith(".md")
    assert payload["review_date"]
    assert "reviewed_skill_drafts" in payload
    assert "promoted_skills" in payload
    assert "open_questions" in payload

    user_memory_response = client.get("/memory/user")
    assert "Prefers local-first workflows" in user_memory_response.json()["content"]


def test_daily_review_endpoint_reports_promoted_skill_drafts(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))
    skill_manager = SkillManager(workspace_paths.skills_dir)
    skill_manager.create_skill_draft(
        name="Review Promotion Candidate",
        description="Draft that should be promoted by daily review.",
        when_to_use="Use this when the workflow was explicitly requested and is stable.",
        inputs=["target path"],
        procedure=["Read the file.", "List the directory.", "Summarize the result."],
        output="A published workflow.",
        metadata={
            "source": "workflow_capture",
            "confidence": 0.92,
            "created_from_sessions": ["session-review-promote"],
            "times_reused": 0,
            "capture_reason": "The user explicitly asked to retain the finished workflow as a skill.",
        },
    )
    client.post(
        "/chat",
        json={"message": "hello", "session_id": "session-review-promote"},
    )

    response = client.post("/reviews/daily")

    assert response.status_code == 200
    payload = response.json()
    assert "Review Promotion Candidate" in payload["promoted_skills"]
    assert any(item["decision"] == "promoted" for item in payload["reviewed_skill_drafts"])


def test_skill_drafts_endpoint_returns_auto_learned_drafts(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))

    client.post(
        "/chat",
        json={
            "message": "Please read `agent.md`, then turn this workflow into skill: Agent Profile Reader",
            "session_id": "session-draft-api",
        },
    )

    response = client.get("/skills/drafts")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["status"] == "draft"
    assert payload[0]["metadata"]["source"] == "workflow_capture"


def test_chat_endpoint_returns_created_skill_draft(settings, workspace_paths) -> None:
    client = TestClient(create_app(settings))

    response = client.post(
        "/chat",
        json={
            "message": "Please read `agent.md`, list the `skills` directory, then turn this workflow into skill: Agent Profile Reader",
            "session_id": "session-draft-inline",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["created_skill_draft"] is not None
    assert payload["created_skill_draft"]["slug"] == "agent_profile_reader"
    assert payload["created_skill_draft"]["status"] == "draft"
    assert payload["created_skill_draft"]["event"] == "created"


def test_provider_settings_endpoint_updates_runtime_and_persists(
    settings,
    workspace_paths,
) -> None:
    app = create_app(settings)
    client = TestClient(app)

    initial = client.get("/settings/provider")
    assert initial.status_code == 200
    assert initial.json()["active_provider"] == "local"

    response = client.post(
        "/settings/provider",
        json={
            "active_provider": "deepseek",
            "model": "deepseek-v4-pro",
            "base_url": "https://api.deepseek.com",
            "api_key": "test-deepseek-key",
            "reasoning_effort": "high",
            "thinking_enabled": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "deepseek"
    assert payload["profiles"]["deepseek"]["has_api_key"] is True
    assert app.state.runtime.provider.name == "deepseek"
    assert workspace_paths.provider_settings_file.exists()

    reloaded_app = create_app(settings)
    reloaded_client = TestClient(reloaded_app)
    reloaded = reloaded_client.get("/settings/provider")

    assert reloaded.status_code == 200
    assert reloaded.json()["active_provider"] == "deepseek"
    assert reloaded_app.state.runtime.provider.name == "deepseek"


def test_provider_settings_endpoint_rejects_unsupported_provider(
    settings,
    workspace_paths,
) -> None:
    client = TestClient(create_app(settings))

    response = client.post(
        "/settings/provider",
        json={"active_provider": "not-a-real-provider"},
    )

    assert response.status_code == 400
    assert "Unsupported provider" in response.json()["detail"]
    assert not workspace_paths.provider_settings_file.exists()
