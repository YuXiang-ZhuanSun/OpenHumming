# OpenHumming

> Small agent. Full loop.

OpenHumming is a local-first Python agent runtime with readable markdown memory,
continuous conversation, skill loading, scheduled task scaffolding, and a
traceable agent loop.

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

This repository ships an MVP foundation:

- `openhumming init` creates a local workspace.
- `openhumming serve` starts a FastAPI server on `127.0.0.1:8765`.
- `POST /chat` loads profiles, recent history, skills, and saves the turn.
- `openhumming chat` provides a local CLI loop.
- Basic file tools, skill management, task storage, and trace recording are
  scaffolded for the next milestones.

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
  -d "{\"message\": \"帮我总结一下 OpenHumming 的目标\"}"
```

Or use the CLI:

```bash
openhumming chat
```

## Repo layout

```txt
openhumming/
├── agent/        # runtime loop, planner, reflection
├── cli/          # Typer commands
├── config/       # settings and logging
├── llm/          # provider abstraction
├── memory/       # profiles, conversation store
├── scheduler/    # task parsing and storage
├── server/       # FastAPI app and routes
├── skills/       # skill loading and creation
├── tools/        # tool protocol and built-ins
├── trace/        # event recording
└── workspace/    # path helpers and initialization
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
