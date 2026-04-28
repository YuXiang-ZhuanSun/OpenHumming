from copy import deepcopy
from pathlib import Path
from textwrap import dedent


_DEFAULT_SHOWCASE = {
    "title": {
        "en": "From seeded workspace to self-improving agent",
        "zh": "从初始工作区到会自我进化的 Agent",
    },
    "subtitle": {
        "en": "A real demo view of how agent.md, user.md, and skills evolve after live conversations and daily review.",
        "zh": "用真实 demo 展示 agent.md、user.md 与 skills 如何在真实对话和每日复盘后发生演化。",
    },
    "items": [
        {
            "id": "agent",
            "label": {"en": "Agent", "zh": "Agent"},
            "before_title": {"en": "Before", "zh": "演化前"},
            "after_title": {"en": "After", "zh": "演化后"},
            "before_path": "examples/real_demos/showcase/agent.before.md",
            "after_path": "examples/real_demos/showcase/agent.after.md",
            "before_content": dedent(
                """
                # Agent Profile

                ## Identity

                I am a local-first autonomous agent runtime.

                ## Behavior Principles

                - Be transparent about actions
                - Prefer local-first execution
                - Ask before risky operations
                - Preserve user intent
                """
            ).strip(),
            "after_content": dedent(
                """
                # Agent Profile

                ## Behavior Principles

                - Be transparent about actions
                - Prefer local-first execution
                - Ask before risky operations
                - Preserve user intent
                - Reference concrete tool outcomes when summarizing tool-assisted work

                ## Working Style

                - Match response depth and pacing to the user's stated collaboration preferences
                """
            ).strip(),
            "highlights": [
                {
                    "en": "The runtime learned a sharper reporting rule after successful tool use.",
                    "zh": "运行时在成功调用工具后学会了更明确的结果汇报规则。",
                },
                {
                    "en": "The agent working style became explicit instead of staying implicit in prompts.",
                    "zh": "Agent 的工作风格不再只是提示词里的隐含约束，而是显式写进了 profile。",
                },
            ],
        },
        {
            "id": "user",
            "label": {"en": "User", "zh": "用户"},
            "before_title": {"en": "Before", "zh": "演化前"},
            "after_title": {"en": "After", "zh": "演化后"},
            "before_path": "examples/real_demos/showcase/user.before.md",
            "after_path": "examples/real_demos/showcase/user.after.md",
            "before_content": dedent(
                """
                # User Profile

                ## Preferences

                - Prefers Python projects
                - Likes structured architectures

                ## Current Projects

                - OpenHumming: a lightweight but complete Python agent runtime
                """
            ).strip(),
            "after_content": dedent(
                """
                # User Profile

                ## Preferences

                - Prefers Python projects
                - Prefers terse engineering updates

                ## Current Projects

                - OpenHumming: a lightweight but complete Python agent runtime
                - Local-first autonomous agent runtime

                ## Interaction Style

                - Prefers direct, implementation-ready planning
                """
            ).strip(),
            "highlights": [
                {
                    "en": "The system retained durable user preferences instead of treating every turn as stateless chat.",
                    "zh": "系统开始保留长期用户偏好，而不是把每轮对话都当成无状态聊天。",
                },
                {
                    "en": "Current project context became queryable memory that can shape later planning.",
                    "zh": "当前项目上下文被沉淀成可检索记忆，后续规划可以直接受它影响。",
                },
            ],
        },
        {
            "id": "skills",
            "label": {"en": "Skills", "zh": "技能"},
            "before_title": {"en": "Before", "zh": "演化前"},
            "after_title": {"en": "After", "zh": "演化后"},
            "before_path": "examples/real_demos/showcase/skills.before.md",
            "after_path": "examples/real_demos/showcase/skills.after.md",
            "before_content": dedent(
                """
                skills/
                |- example_skill.md
                `- drafts/
                   `- README.md
                """
            ).strip(),
            "after_content": dedent(
                """
                skills/
                |- example_skill.md
                |- workspace_orientation.md
                `- drafts/
                   `- README.md

                ---
                status: "published"
                source: "workflow_capture"
                confidence: 0.92
                promoted_by: "daily_review"
                ---
                # Skill: Workspace Orientation
                """
            ).strip(),
            "highlights": [
                {
                    "en": "A multi-step workflow was captured as a draft and then promoted by daily review.",
                    "zh": "一个多步骤工作流先被学习成 draft，再由 daily review 晋升为正式 skill。",
                },
                {
                    "en": "The skill library is no longer static documentation; it is a living artifact of work completed.",
                    "zh": "技能库不再只是静态文档，而是任务完成后持续生长的工作资产。",
                },
            ],
        },
    ],
}


def load_evolution_showcase() -> dict[str, object]:
    payload = deepcopy(_DEFAULT_SHOWCASE)
    repo_root = Path(__file__).resolve().parents[2]
    for item in payload["items"]:
        before_path = repo_root / item["before_path"]
        after_path = repo_root / item["after_path"]
        if before_path.exists():
            item["before_content"] = before_path.read_text(encoding="utf-8").strip()
        if after_path.exists():
            item["after_content"] = after_path.read_text(encoding="utf-8").strip()
    return payload
