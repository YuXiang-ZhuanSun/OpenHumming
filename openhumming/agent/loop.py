from openhumming.memory.store import MemoryContext
from openhumming.skills.loader import SkillDocument


def build_system_prompt(
    context: MemoryContext,
    relevant_skills: list[SkillDocument],
) -> str:
    skill_section = "\n".join(
        f"- {skill.name}: {skill.description or 'No description provided.'}"
        for skill in relevant_skills
    ) or "- No directly matched skills."

    return (
        "You are OpenHumming, a local-first Python agent runtime.\n\n"
        "## Agent Profile\n"
        f"{context.agent_profile}\n\n"
        "## User Profile\n"
        f"{context.user_profile}\n\n"
        "## Relevant Skills\n"
        f"{skill_section}\n\n"
        "Be transparent about actions, preserve user intent, and prefer local-first execution."
    )
