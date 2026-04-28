# Skill System / 技能系统

OpenHumming separates published skills from learned drafts.  
OpenHumming 把正式技能与学习草稿明确分开。

- `workspace/skills/*.md`: published skills the runtime can retrieve during chat  
  `workspace/skills/*.md`：运行时在对话中可直接检索的正式技能
- nested folders under `workspace/skills/`: extension packs for organizing larger skill libraries  
  `workspace/skills/` 下的嵌套目录：用来组织更大技能库的 extension pack
- `workspace/skills/drafts/*.md`: auto-learned workflow drafts waiting for review  
  `workspace/skills/drafts/*.md`：自动学习到、等待复盘审核的工作流草稿

## What a Skill Contains / 一个 Skill 包含什么

Each skill or draft should answer:  
每个 skill 或 draft 都应该回答：

- What problem it solves / 它解决什么问题
- When to use it / 什么时候使用
- What inputs it expects / 需要哪些输入
- What procedure it follows / 它遵循什么步骤
- What output it should produce / 它最终产出什么

## Draft Metadata / 草稿元数据

Drafts carry frontmatter metadata so the system can explain where they came from.  
草稿会携带 frontmatter 元数据，让系统能解释它从哪里来。

- `status`
- `source`
- `created_from_sessions`
- `confidence`
- `times_reused`
- `capture_reason`

`times_reused` now grows when the same workflow succeeds again, which gives daily review stronger evidence for promotion.  
`times_reused` 会在同一工作流再次成功时增长，为 daily review 晋升提供更强证据。

## Current Loop / 当前闭环

The runtime can now:  
当前运行时已经可以：

- retrieve published skills during the main agent loop  
  在主对话循环中检索正式技能
- create published skills through the API or tool layer  
  通过 API 或工具层创建正式技能
- capture completed workflows as reusable drafts  
  把已完成工作流捕获成可复用草稿
- refresh existing drafts when the same workflow succeeds again  
  当同一工作流再次成功时，更新已有草稿并累计复用证据
- expose draft inventory through `GET /skills/drafts`  
  通过 `GET /skills/drafts` 暴露草稿队列
- review drafts during daily review  
  在 daily review 中审核草稿
- promote strong drafts into `workspace/skills/`  
  把强草稿晋升到 `workspace/skills/`

## Philosophy / 设计哲学

Skill growth should be visible, reviewable, and incremental.  
技能增长应该是可见的、可审核的、渐进式的。
