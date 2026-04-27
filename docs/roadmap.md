# Roadmap

## Completed Milestones

### v0.1

- Local workspace initialization
- FastAPI chat endpoint
- CLI chat loop
- Profile loading and conversation persistence
- Local provider fallback

### v0.2

- Tool registry and real tool execution inside the runtime loop
- Trace recording for tool calls and turn lifecycle events

### v0.3

- Skill retrieval from workspace markdown
- Skill context injection into the runtime prompt

### v0.4

- Skill candidate detection
- Automatic skill draft generation and persistence

### v0.5

- APScheduler-backed background task runner
- Task-triggered runtime execution
- Task run logging under `workspace/tasks/runs/`

### v0.6

- Daily review summaries
- Stable memory extraction for `user.md`
- Capability refreshes for `agent.md`
- Manual and scheduled review entrypoints

## v1.0 Finish Line

- Polished README and documentation set
- CI validation on push and pull request
- Release tags and changelog discipline
- More demos and examples
- Optional skill marketplace primitives

## Longer-Term Ideas

- Safer approval-aware shell execution
- Vector or hybrid skill retrieval
- Multi-agent collaboration patterns
- Browser and Git integrations
- Skill export and sharing flows
