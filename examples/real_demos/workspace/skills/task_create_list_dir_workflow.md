---
status: "published"
source: "workflow_capture"
created_from_sessions: ["demo-task"]
confidence: 0.78
times_reused: 0
capture_reason: "The workflow succeeded, has stable inputs, and looks reusable."
promoted_on: "2026-04-28"
promoted_by: "daily_review"
promotion_reason: "The draft was created from today's work and has enough confidence to publish."
---
# Skill: task_create_list_dir_workflow

## Description

Reusable schedule_task workflow using task_create, list_dir.

## When to Use

Use this when the user wants to create or manage a recurring task.

## Inputs

- user goal
- workspace context
- schedule request
- target path

## Procedure

1. Understand the user's intended outcome.
2. Detected a scheduling request.
3. Directory listing requested for ..
4. Run `task_create` and verify the outcome: review the workspace skills directory..
5. Run `list_dir` and verify the outcome: [{'name': 'agent.md', 'is_dir': False}, {'name': 'config', 'is_dir': True}, {'name': 'conversations', 'is_dir': True}....
6. Summarize the outcome and explain the next useful step.

## Output

A created task definition and a concise explanation of the schedule.
