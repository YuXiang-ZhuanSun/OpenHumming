import re

from openhumming.agent.state import ToolCallPlan, TurnPlan
from openhumming.skills.loader import SkillDocument

READ_HINTS = (
    "read",
    "open",
    "show",
    "\u8bfb\u53d6",
    "\u67e5\u770b",
    "\u6253\u5f00",
)
LIST_HINTS = ("list", "ls", "\u5217\u51fa")
WRITE_HINTS = (
    "write",
    "save",
    "\u5199\u5165",
    "\u4fdd\u5b58",
    "\u521b\u5efa\u6587\u4ef6",
)
SCHEDULE_HINTS = (
    "\u6bcf\u5929",
    "\u6bcf\u5468",
    "every day at",
)
SKILL_HINTS = ("skill", "\u6280\u80fd", "\u6d41\u7a0b")
SKILL_READ_HINTS = ("read skill", "show skill", "\u67e5\u770b skill", "\u8bfb\u53d6 skill")
FILE_PATTERN = re.compile(
    r"`([^`]+)`|([A-Za-z0-9_./\\\\-]+\.[A-Za-z0-9_]+)|"
    r"(workspace[./\\\\A-Za-z0-9_-]+)"
)
DIRECTORY_PATTERN = re.compile(
    r"`([^`]+)`\s+(?:directory|folder)|"
    r"(?:directory|folder)\s+`([^`]+)`|"
    r"(?:list|show|inspect)\s+(?:the\s+)?([A-Za-z0-9_./\\\\-]+)\s+(?:directory|folder)",
    re.IGNORECASE,
)
CONTENT_PATTERN = re.compile(
    r"(?:content|contents|\u5185\u5bb9)\s*[:\uff1a]?\s*(.+)$",
    re.IGNORECASE,
)
SCHEDULE_PATTERN = re.compile(
    r"((?:\u6bcf\u5929|\u6bcf\u5468[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u65e5\u5929]?|every day at).+)",
    re.IGNORECASE,
)
SKILL_NAME_PATTERN = re.compile(
    r"(?:\bskill\b|\u6280\u80fd)\s*[:\uff1a]\s*`?([A-Za-z0-9_\-\u4e00-\u9fff ]+)`?$",
    re.IGNORECASE,
)


class Planner:
    def plan(self, message: str, skills: list[SkillDocument]) -> TurnPlan:
        lowered = message.lower()
        relevant = [
            skill.name
            for skill in skills
            if self._skill_matches_message(skill, message)
        ][:3]

        tool_calls: list[ToolCallPlan] = []
        notes: list[str] = []

        schedule_text = self._extract_schedule_text(message)
        if schedule_text:
            tool_calls.append(
                ToolCallPlan(
                    tool_name="task_create",
                    input_data={"natural_language": schedule_text},
                    reason="User requested a scheduled task.",
                )
            )
            notes.append("Detected a scheduling request.")

        if self._contains_any(lowered, LIST_HINTS):
            directory = self._extract_directory_path(message) or self._extract_path(message) or "."
            tool_calls.append(
                ToolCallPlan(
                    tool_name="list_dir",
                    input_data={"path": directory},
                    reason="User asked to inspect a directory.",
                )
            )
            notes.append(f"Directory listing requested for {directory}.")

        if self._contains_any(lowered, READ_HINTS):
            if self._contains_any(lowered, SKILL_READ_HINTS):
                skill_name = self._extract_skill_name(message)
                if skill_name:
                    tool_calls.append(
                        ToolCallPlan(
                            tool_name="skill_read",
                            input_data={"name": skill_name},
                            reason="User asked to read a skill document.",
                        )
                    )
                    notes.append(f"Skill read requested for {skill_name}.")
            else:
                path = self._extract_path(message)
                if path:
                    tool_calls.append(
                        ToolCallPlan(
                            tool_name="file_read",
                            input_data={"path": path},
                            reason="User asked to read a file.",
                        )
                    )
                    notes.append(f"File read requested for {path}.")

        if self._contains_any(lowered, WRITE_HINTS):
            path = self._extract_path(message)
            content = self._extract_content(message)
            if path and content is not None:
                tool_calls.append(
                    ToolCallPlan(
                        tool_name="file_write",
                        input_data={"path": path, "content": content},
                        reason="User asked to write a file.",
                    )
                )
                notes.append(f"File write requested for {path}.")

        intent = self._infer_intent(lowered, schedule_text, tool_calls)
        return TurnPlan(
            intent=intent,
            relevant_skills=relevant,
            tool_calls=self._deduplicate_tool_calls(tool_calls),
            notes=notes,
        )

    def _contains_any(self, text: str, hints: tuple[str, ...]) -> bool:
        return any(hint.lower() in text for hint in hints)

    def _extract_path(self, message: str) -> str | None:
        for match in FILE_PATTERN.finditer(message):
            for group in match.groups():
                if group and self._looks_like_path(group):
                    return group.replace("\\", "/")
        return None

    def _extract_directory_path(self, message: str) -> str | None:
        match = DIRECTORY_PATTERN.search(message)
        if match:
            for group in match.groups():
                if group:
                    return group.replace("\\", "/")
        return None

    def _extract_content(self, message: str) -> str | None:
        match = CONTENT_PATTERN.search(message)
        if match:
            return match.group(1).strip()
        return None

    def _extract_schedule_text(self, message: str) -> str | None:
        match = SCHEDULE_PATTERN.search(message)
        if not match:
            return None
        return match.group(1).strip(" \u3002\uff01?!")

    def _extract_skill_name(self, message: str) -> str | None:
        match = SKILL_NAME_PATTERN.search(message.strip())
        if match:
            return match.group(1).strip()
        backticked = re.findall(r"`([^`]+)`", message)
        if backticked:
            return backticked[0].strip()
        return None

    def _infer_intent(
        self,
        lowered: str,
        schedule_text: str | None,
        tool_calls: list[ToolCallPlan],
    ) -> str:
        if schedule_text:
            return "schedule_task"
        if tool_calls:
            return "tool_use"
        if self._contains_any(lowered, SKILL_HINTS):
            return "skill_work"
        return "chat"

    def _skill_matches_message(self, skill: SkillDocument, message: str) -> bool:
        lowered_message = message.lower()
        lowered_content = skill.content.lower()
        lowered_name = skill.name.lower()
        return (
            lowered_name in lowered_message
            or skill.slug.lower() in lowered_message
            or any(
                token in lowered_content
                for token in self._query_tokens(message)
                if len(token) > 2
            )
        )

    def _query_tokens(self, message: str) -> set[str]:
        return {token.lower() for token in re.findall(r"[A-Za-z0-9_]+", message)}

    def _looks_like_path(self, value: str) -> bool:
        return (
            "/" in value
            or "\\" in value
            or "." in value
            or value.startswith("workspace")
        )

    def _deduplicate_tool_calls(
        self,
        tool_calls: list[ToolCallPlan],
    ) -> list[ToolCallPlan]:
        seen: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
        unique: list[ToolCallPlan] = []
        for call in tool_calls:
            signature = (
                call.tool_name,
                tuple(sorted((key, str(value)) for key, value in call.input_data.items())),
            )
            if signature in seen:
                continue
            seen.add(signature)
            unique.append(call)
        return unique
