# Real Demo Suite

This directory holds a repeatable end-to-end demo harness for the local HTTP runtime.
It exists to answer a simple question: does OpenHumming still feel convincing when it runs through real scenarios instead of unit tests?

## Included Artifacts

- `demo_suite.json`: end-to-end scenarios covering chat, tools, memory, skill drafting, reuse, and daily review
- `workspace/`: disposable workspace used by the demo harness
- `last_run_report.md`: generated report from the latest run
- `showcase/`: before and after snapshots for the evolution narrative

## Run It

```bash
python scripts/run_real_demos.py
```

## What A Good Demo Run Proves

- the runtime can answer through a real local port
- tool-assisted turns are persisted to conversations and traces
- preferences can land in `user.md`
- working style can land in `agent.md`
- reusable workflows can become draft or published skills
- daily review can summarize the day and close the loop

## Suggested Use

- use `last_run_report.md` when preparing a release post or demo recording
- use `showcase/` when you want before and after evidence for the homepage story
- rerun the suite before opening a release PR or publishing a new tag
