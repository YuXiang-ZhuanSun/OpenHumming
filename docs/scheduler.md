# Scheduler

The scheduler module is scaffolded around three concepts:

- Parse natural-language scheduling text into a cron expression
- Persist tasks in `workspace/tasks/tasks.json`
- Trigger prompts back into the agent runtime

This repository includes the task parser and storage layer first. APScheduler
integration can be added without reshaping the data model.
