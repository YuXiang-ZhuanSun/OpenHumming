# Memory System / 记忆系统

OpenHumming uses markdown for durable memory and JSONL for event-like history.  
OpenHumming 使用 Markdown 作为长期记忆载体，使用 JSONL 作为事件型历史记录。

- `workspace/agent.md`: long-lived agent identity, behavior, and working style  
  `workspace/agent.md`：长期 Agent 身份、行为与工作风格
- `workspace/user.md`: durable user preferences and project context  
  `workspace/user.md`：长期用户偏好与项目背景
- `workspace/conversations/*.jsonl`: turn-level chat history  
  `workspace/conversations/*.jsonl`：逐轮对话历史
- `workspace/summaries/*.md`: daily review outputs  
  `workspace/summaries/*.md`：每日复盘输出

## Turn-Level Memory / 逐轮记忆

On each turn the runtime can:  
在每一轮对话中，runtime 可以：

- Read `agent.md` and `user.md` before answering.  
  在回答前读取 `agent.md` 与 `user.md`。
- Generate structured memory proposals from the latest message.  
  根据最新消息生成结构化记忆提案。
- Apply safe markdown updates when a proposal is stable and new.  
  当提案既稳定又是新增时，安全地写回 Markdown。
- Replace stale interaction-style bullets when newer user guidance supersedes them.  
  当更新的协作偏好覆盖旧设定时，系统会替换旧记忆条目，而不是只不断追加。

## Daily Review Memory / 每日复盘记忆

Daily review still matters even after turn-level writes.  
即使已经支持逐轮写回，每日复盘依然重要。

It can:  
它可以：

- backfill durable user preferences that were only present in logs  
  回填那些只出现在日志里的长期用户偏好
- refresh agent profile capabilities  
  刷新 Agent profile 的能力条目
- reconcile newer collaboration preferences against older `agent.md` and `user.md` entries  
  根据更新的协作偏好对 `agent.md` 和 `user.md` 中旧有条目做对照与替换
- review learned skill drafts and promote strong ones  
  审核学到的技能草稿，并晋升强草稿
- record open questions for future clarification  
  记录后续仍需确认的问题

## Why Files Matter / 为什么文件很重要

The memory model is intentionally simple: files you can inspect, diff, edit, and carry between machines.  
记忆模型刻意保持简单：所有关键状态都应该是你能检查、diff、编辑、跨机器迁移的文件。
