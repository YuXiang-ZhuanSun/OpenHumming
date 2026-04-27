from openhumming.agent.state import TurnObservation, TurnPlan
from openhumming.memory.store import MemoryContext
from openhumming.skills.loader import SkillDocument


def build_system_prompt(
    context: MemoryContext,
    relevant_skills: list[SkillDocument],
    plan: TurnPlan,
    observation: TurnObservation,
) -> str:
    skill_section = "\n\n".join(
        _render_skill_context(skill)
        for skill in relevant_skills
    ) or "- No directly matched skills."

    notes_section = "\n".join(f"- {note}" for note in plan.notes) or "- No planner notes."

    return (
        "You are OpenHumming, a local-first Python agent runtime.\n\n"
        "## Agent Profile\n"
        f"{context.agent_profile}\n\n"
        "## User Profile\n"
        f"{context.user_profile}\n\n"
        "## Intent\n"
        f"{plan.intent}\n\n"
        "## Planner Notes\n"
        f"{notes_section}\n\n"
        "## Relevant Skills\n"
        f"{skill_section}\n\n"
        "## Tool Results\n"
        f"{observation.summary}\n\n"
        "Be transparent about actions, preserve user intent, prefer local-first "
        "execution, and mention concrete tool outcomes when tools were used."
    )


def _render_skill_context(skill: SkillDocument) -> str:
    content = skill.content.strip()
    if len(content) > 1200:
        content = content[:1197].rstrip() + "..."
    return f"### {skill.name}\n{content}"
