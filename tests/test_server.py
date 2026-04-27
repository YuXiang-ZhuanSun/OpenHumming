from fastapi.testclient import TestClient

from openhumming.server.app import create_app


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

    memory_response = client.get("/memory/agent")
    assert memory_response.status_code == 200
    assert "OpenHumming" in memory_response.json()["content"]

    conversation_file = workspace_paths.conversation_file()
    assert conversation_file.exists()
