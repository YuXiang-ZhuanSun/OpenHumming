# Architecture

OpenHumming is organized around a simple but complete agent loop:

1. Load workspace context from `agent.md`, `user.md`, conversation history, and skills.
2. Build a turn plan.
3. Optionally execute tools.
4. Observe outputs and record trace events.
5. Reflect on whether the turn suggests memory, skill, or task updates.
6. Respond and persist the result.

The MVP keeps the planner and reflection layers intentionally lightweight, but
the module boundaries are already in place so later versions can deepen the
loop without a repo rewrite.
