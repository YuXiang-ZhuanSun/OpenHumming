from openhumming.memory.store import MemoryStore


def test_memory_store_loads_profiles_and_turns(workspace_paths) -> None:
    store = MemoryStore(workspace_paths)
    initial_context = store.load_context()

    assert "OpenHumming" in initial_context.agent_profile
    assert "Python" in initial_context.user_profile
    assert initial_context.conversation_history == []

    store.save_turn("session-a", "hello", "world", metadata={"intent": "chat"})
    updated_context = store.load_context(session_id="session-a")

    assert [item.role for item in updated_context.conversation_history] == [
        "user",
        "assistant",
    ]
    assert updated_context.conversation_history[0].content == "hello"
    assert updated_context.conversation_history[1].content == "world"
