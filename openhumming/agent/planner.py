from openhumming.agent.state import TurnPlan
from openhumming.skills.loader import SkillDocument


class Planner:
    def plan(self, message: str, skills: list[SkillDocument]) -> TurnPlan:
        lowered = message.lower()
        relevant = [
            skill.name
            for skill in skills
            if skill.slug.lower() in lowered or skill.name.lower() in lowered
        ][:3]

        if any(keyword in message for keyword in ("每天", "每周")) or "schedule" in lowered:
            intent = "schedule_task"
        elif any(keyword in message for keyword in ("skill", "技能", "沉淀", "流程")):
            intent = "skill_work"
        else:
            intent = "chat"

        return TurnPlan(
            intent=intent,
            relevant_skills=relevant,
            needs_tool_execution=False,
        )
