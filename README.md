# OpenHumming

> Small agent. Full loop.

OpenHumming is a local-first Python agent runtime with readable markdown
memory, continuous conversation, real tool execution, reusable skills,
scheduled tasks, and daily review.

## Why it exists

Most agent demos stop at "send prompt, get answer". OpenHumming aims for a
smaller but more complete loop:

- `agent.md` defines the agent identity.
- `user.md` captures stable user preferences.
- Conversations are persisted as JSONL.
- Skills live as markdown files in the workspace.
- Tasks can be created from natural-language scheduling prompts.
- Every turn can be traced for later inspection.

## Current status

This repository now covers the roadmap from `v0.1` through `v0.6`:

- `openhumming init` creates a local workspace.
- `openhumming serve` starts a FastAPI server on `127.0.0.1:8765`.
- `POST /chat` loads profiles, history, skills, runs tools, and saves the turn.
- `openhumming chat` provides a local CLI loop.
- Reusable workflows can be auto-saved as markdown skills.
- Scheduled tasks run in the background and write run logs.
- `openhumming daily-review` writes daily summaries and updates memory.

By default the runtime uses a deterministic local provider so the project works
without an API key. You can switch to OpenAI or Anthropic by configuring
environment variables.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
openhumming init
openhumming serve
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Help me summarize the goals of OpenHumming\"}"
```

Or use the CLI:

```bash
openhumming chat
openhumming daily-review
```

## Repo layout

```txt
openhumming/
|-- agent/        # runtime loop, planner, execution, reflection
|-- cli/          # Typer commands
|-- config/       # settings and logging
|-- llm/          # provider abstraction
|-- memory/       # profiles, conversation store, daily review
|-- scheduler/    # task parsing, scheduling, run logging
|-- server/       # FastAPI app and routes
|-- skills/       # skill loading, retrieval, and creation
|-- tools/        # tool protocol and built-ins
|-- trace/        # event recording
`-- workspace/    # path helpers and initialization
```

## Philosophy

Minimal core.
Readable memory.
Evolving skills.
Full agent loop.

## Roadmap

- v0.1 Local chat loop
- v0.2 Tool execution
- v0.3 Skill-aware runtime
- v0.4 Automatic skill creation
- v0.5 Scheduled tasks
- v0.6 Daily review and memory updates
- v1.0 Documentation, CI, demos, packaging polish

See [docs/roadmap.md](/C:/Users/Xiang/Downloads/projects/SwiftAgent/docs/roadmap.md)
for more detail.
