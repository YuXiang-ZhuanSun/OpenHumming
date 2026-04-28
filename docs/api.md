# API / 接口

## `POST /chat`

Send one user message through the runtime loop.  
向运行时发送一条用户消息并执行完整闭环。

Request / 请求：

```json
{
  "message": "Help me summarize what we finished today",
  "session_id": "optional-session-id"
}
```

Response / 响应：

```json
{
  "session_id": "generated-or-provided-id",
  "response": "assistant reply",
  "actions": ["load_profiles", "load_history", "record_conversation"],
  "memory_updates": {
    "agent": false,
    "user": false
  },
  "memory_proposals": [
    {
      "target": "user",
      "section": "## Preferences",
      "content": "Prefers implementation-ready updates",
      "reason": "Detected an explicit long-term user preference in the latest turn.",
      "confidence": 0.84
    }
  ],
  "applied_memory_updates": [
    {
      "target": "user",
      "section": "## Preferences",
      "content": "Prefers implementation-ready updates",
      "path": "/absolute/path/to/workspace/user.md"
    }
  ],
  "created_skill_draft": {
    "name": "Agent Profile Reader",
    "slug": "agent_profile_reader",
    "description": "Reusable tool_use workflow using file_read, list_dir.",
    "path": "/absolute/path/to/workspace/skills/drafts/agent_profile_reader.md",
    "status": "draft",
    "metadata": {
      "source": "workflow_capture",
      "confidence": 0.92
    }
  }
}
```

Notes / 说明：

- `memory_proposals` describes what the runtime inferred from the latest turn.  
  `memory_proposals` 描述运行时从本轮对话中推断出的长期记忆提案。
- `applied_memory_updates` lists the profile changes that were actually written.  
  `applied_memory_updates` 列出真正写回 profile 的变更。
- `memory_updates` is the quick boolean summary.  
  `memory_updates` 是给客户端快速判断用的布尔摘要。
- `created_skill_draft` appears when the runtime captures a reusable workflow draft.  
  `created_skill_draft` 会在运行时捕获到可复用工作流草稿时出现。

## `GET /skills`

List published skills.  
列出已发布技能。

## `GET /skills/drafts`

List learned skill drafts waiting for review.  
列出等待复盘审核的技能草稿。

## `POST /skills`

Create a published skill from structured input.  
通过结构化输入创建一个正式发布的技能。

## `GET /tasks`

List persisted scheduled tasks.  
列出已持久化的定时任务。

## `POST /tasks`

Create a task from natural-language schedule text.  
通过自然语言调度描述创建任务。

## `POST /reviews/daily`

Run daily review immediately.  
立即执行每日复盘。

The response includes:  
响应中还会包含：

- `summary_path`: the daily markdown report path  
  `summary_path`：每日 Markdown 报告路径
- `user_updates` / `agent_updates`: profile updates applied during review  
  `user_updates` / `agent_updates`：复盘期间应用的 profile 更新
- `reviewed_skill_drafts`: each reviewed draft plus its decision  
  `reviewed_skill_drafts`：每个被审核的 draft 及其决策
- `promoted_skills`: names of drafts promoted to published skills  
  `promoted_skills`：被晋升为正式技能的草稿名
- `open_questions`: review items that still need more evidence  
  `open_questions`：仍需更多证据的复盘问题

## `GET /memory/agent`

Return the current `agent.md` content.  
返回当前 `agent.md` 内容。

## `GET /memory/user`

Return the current `user.md` content.  
返回当前 `user.md` 内容。

## `GET /showcase/evolution`

Return the before/after showcase payload used by the local UI.  
返回本地 UI 使用的 before/after 演化展示数据。

## `GET /ui`

Open the lightweight local console.  
打开轻量本地控制台页面。

## `GET /settings/provider`

Return the active provider plus saved provider profiles for the local workspace UI.  
返回当前激活的 provider 以及工作区里保存的 provider 配置。

## `POST /settings/provider`

Update the active provider profile and hot-swap the runtime backend without restarting the server.  
更新当前激活的 provider 配置，并在不重启服务的情况下热切换运行时后端。
