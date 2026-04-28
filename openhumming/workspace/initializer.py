from pathlib import Path

from openhumming.workspace.paths import WorkspacePaths

DEFAULT_AGENT_PROFILE = """# Agent Profile

## Name

OpenHumming

## Identity

I am a local-first autonomous agent runtime.

## Capabilities

- Read and write files inside the workspace
- Inspect directories
- Load and create markdown skills
- Persist conversations and traces
- Store scheduled task definitions
- Execute scheduled tasks
- Create skills from repeated workflows
- Review daily conversations and update memory

## Behavior Principles

- Be transparent about actions
- Prefer local-first execution
- Ask before risky operations
- Preserve user intent
"""

DEFAULT_USER_PROFILE = """# User Profile

## Preferences

- Prefers Python projects
- Likes structured architectures
- Values reusable workflows

## Current Projects

- OpenHumming: a lightweight but complete Python agent runtime

## Interaction Style

- Prefers direct, implementation-ready planning
"""

DEFAULT_SKILLS_README = """# Workspace Skills

Store reusable workflow skills here as markdown files.
把可复用的工作流技能以 Markdown 文件形式放在这里。
"""

DEFAULT_SKILL_DRAFTS_README = """# Skill Drafts

Auto-learned workflow drafts land here before they are promoted to published skills.
自动学习得到的工作流草稿会先落在这里，等通过复盘审核后再晋升为正式技能。
"""

DEFAULT_EXAMPLE_SKILL = """# Skill: Create Agent Project Plan

## Description

Create a mature project plan for a Python-based agent runtime.

## When to Use

Use this skill when the user wants to design or scaffold an agent project.

## Inputs

- project name
- target language
- core features
- repo style

## Procedure

1. Clarify the goal.
2. Design the architecture.
3. Define module responsibilities.
4. Propose the directory structure.
5. Define the MVP.
6. Define the roadmap.

## Output

A complete implementation-ready project plan.
"""


def _write_if_needed(path: Path, content: str, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def initialize_workspace(paths: WorkspacePaths, overwrite: bool = False) -> list[str]:
    created: list[str] = []
    for directory in paths.directories:
        directory.mkdir(parents=True, exist_ok=True)

    files_to_seed = {
        paths.agent_profile: DEFAULT_AGENT_PROFILE,
        paths.user_profile: DEFAULT_USER_PROFILE,
        paths.skills_dir / "README.md": DEFAULT_SKILLS_README,
        paths.skill_drafts_dir / "README.md": DEFAULT_SKILL_DRAFTS_README,
        paths.skills_dir / "example_skill.md": DEFAULT_EXAMPLE_SKILL,
        paths.tasks_file: "[]\n",
    }

    for file_path, content in files_to_seed.items():
        if _write_if_needed(file_path, content, overwrite):
            created.append(str(file_path))

    return created
