# Scheduler / 调度系统

The scheduler turns natural-language recurring requests into live runtime work.  
调度系统负责把自然语言的周期性请求变成真正运行中的任务。

## What It Does / 它负责什么

- Parse natural-language scheduling text into cron-like schedules.  
  把自然语言调度文本解析成类似 cron 的调度表达。
- Persist task definitions in `workspace/tasks/tasks.json`.  
  把任务定义持久化到 `workspace/tasks/tasks.json`。
- Trigger prompts back into the agent runtime on schedule.  
  在预定时间把 prompt 再次送回 Agent runtime。
- Record task runs under `workspace/tasks/runs/`.  
  在 `workspace/tasks/runs/` 下记录任务执行历史。
- Optionally trigger daily review every day.  
  也可以每天自动触发 daily review。

## Current Status / 当前状态

This is no longer a scaffold.  
它现在已经不只是脚手架。

OpenHumming already ships:  
OpenHumming 已经提供：

- a natural-language task parser  
  自然语言任务解析器
- persistent task storage  
  任务持久化存储
- APScheduler-backed background execution  
  基于 APScheduler 的后台执行
- run logs and daily review integration  
  运行日志与 daily review 集成
