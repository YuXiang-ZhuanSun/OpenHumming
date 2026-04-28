---
status: "published"
source: "workflow_capture"
created_from_sessions: ["demo-skill-draft", "demo-skill-reuse"]
confidence: 0.92
times_reused: 1
capture_reason: "The user explicitly asked to retain the finished workflow as a skill."
promoted_on: "2026-04-28"
promoted_by: "daily_review"
promotion_reason: "The draft came from an explicit user request and has high capture confidence."
---
# Skill: Workspace Orientation

## Description

Reusable tool_use workflow using list_dir, file_read.

## When to Use

Use this when the user asks for a repeatable workspace operation.

## Inputs

- user goal
- workspace context
- target path

## Procedure

1. Understand the user's intended outcome.
2. Directory listing requested for skills.
3. File read requested for agent.md.
4. Run `list_dir` and verify the outcome: [{'name': 'drafts', 'is_dir': True}, {'name': 'example_skill.md', 'is_dir': False}, {'name': 'README.md', 'is_dir': F....
5. Run `file_read` and verify the outcome: # Agent Profile  ## Name  OpenHumming  ## Identity  I am a local-first autonomous agent runtime.  ## Capabilities  -....
6. Summarize the outcome and explain the next useful step.

## Output

A completed workflow result plus a concise explanation of what was done.
