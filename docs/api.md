# API

## `POST /chat`

Send one user message through the runtime loop.

Request:

```json
{
  "message": "Help me summarize what we finished today",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "session_id": "generated-or-provided-id",
  "response": "assistant reply",
  "actions": ["load_profiles", "load_history", "record_conversation"],
  "memory_updates": {
    "agent": false,
    "user": false
  }
}
```

## `GET /skills`

List available skills in the workspace.

## `POST /skills`

Create a skill markdown file from structured input.

## `GET /tasks`

List persisted scheduled tasks.

## `POST /tasks`

Create a task from natural-language schedule text.

## `POST /reviews/daily`

Run a daily review immediately. This writes a summary markdown file and applies
stable memory updates to `agent.md` and `user.md`.
