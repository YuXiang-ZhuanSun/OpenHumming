# Showcase

![OpenHumming showcase](assets/openhumming-showcase.svg)

OpenHumming ships a dedicated evolution showcase for the most important artifacts in the workspace.
It is the fastest way to understand what the runtime actually learns after live interaction.

## Where To Look

- Local UI: `http://127.0.0.1:8765/ui`
- JSON endpoint: `GET /showcase/evolution`
- Real demo snapshots: `examples/real_demos/showcase/`

## What It Compares

- `agent.md` before and after real tool-assisted work
- `user.md` before and after memory consolidation
- `skills/` before and after workflow learning plus daily review

## What The Viewer Should Notice

### `agent.md`

The runtime should not keep its collaboration style implicit forever.
After real usage, `agent.md` becomes more specific about how the system should report outcomes and adapt to the user.

### `user.md`

The user profile should become more concrete after real conversation.
The showcase is strongest when it demonstrates sharper interaction preferences or project context than the seeded workspace had at the start.

### `skills/`

This is where the product story becomes obvious.
The showcase should reveal that repeated work did not disappear into logs: it became a draft, gathered reuse evidence, and then turned into a published skill.

## Why It Matters

The showcase answers the three questions that matter most for a project like this:

1. Did the runtime actually learn anything?
2. Did memory become more specific after interaction?
3. Did repeated work become a reusable artifact?

If the answer is yes across those three cards, the project story becomes self-evident in a few seconds.
