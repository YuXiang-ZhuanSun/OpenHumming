# API

## `POST /chat`

Send one user message through the runtime loop.

Request:

```json
{
  "message": "帮我总结今天做了什么",
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
