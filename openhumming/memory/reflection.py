import re

from openhumming.agent.state import TurnObservation, TurnPlan
from openhumming.memory.models import MemoryUpdateProposal

USER_PREFERENCE_PATTERNS = (
    re.compile(r"(?:remember(?: that)?|i prefer|i like)\s+([^.!?\n]+)", re.IGNORECASE),
    re.compile(
        r"(?:记住我(?:的)?(?:偏好|喜欢)?|我(?:偏好|喜欢|更喜欢))([^。！\n]+)"
    ),
)
USER_PROJECT_PATTERNS = (
    re.compile(
        r"(?:i(?:'m| am) working on|i(?:'m| am) building|my project is)\s+([^.!?\n]+)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:我在做|我在构建|我的项目是)([^。！\n]+)"),
)
INTERACTION_STYLE_KEYWORDS = (
    "concise",
    "brief",
    "direct",
    "implementation-ready",
    "step-by-step",
    "detailed",
    "actionable",
    "structured",
    "terse",
    "简洁",
    "直接",
    "可执行",
    "详细",
    "分步",
    "结构化",
    "简短",
)
INTERACTION_STYLE_HINTS = (
    "response",
    "responses",
    "update",
    "updates",
    "planning",
    "plan",
    "explanation",
    "explanations",
    "answer",
    "answers",
    "回复",
    "说明",
    "解释",
    "计划",
    "更新",
)
INTERACTION_REQUEST_PATTERNS = (
    re.compile(
        r"(?:please\s+)?(?:give|keep|make|write|answer|respond)(?:\s+me)?\s+"
        r"([^.!?\n]*?(?:updates?|responses?|answers?|planning|plans|explanations?)[^.!?\n]*)"
        r"(?:\s+from now on)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:from now on|going forward),?\s*(?:please\s+)?"
        r"(?:keep|make|write|answer|respond)\s+([^.!?\n]+)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:从现在开始|以后)(?:请)?([^。！？\n]*?(?:回复|更新|解释|说明|计划)[^。！？\n]*)"),
    re.compile(r"(?:请)(?:给我|保持|使用)?([^。！？\n]*?(?:回复|更新|解释|说明|计划)[^。！？\n]*)"),
)


class MemoryReflectionEngine:
    def propose(
        self,
        *,
        message: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> list[MemoryUpdateProposal]:
        proposals = self.propose_from_message(message)
        proposals.extend(self._propose_agent_tool_reporting(plan, observation))
        return self._deduplicate(proposals)

    def propose_from_message(self, message: str) -> list[MemoryUpdateProposal]:
        preferences = self._extract_preferences(message)
        interaction_styles = self._extract_interaction_styles(message, preferences)

        proposals: list[MemoryUpdateProposal] = []
        proposals.extend(self._propose_user_preferences(preferences))
        proposals.extend(self._propose_user_projects(message))
        proposals.extend(self._propose_user_interaction_style(interaction_styles))
        proposals.extend(self._propose_agent_working_style(interaction_styles))
        return self._deduplicate(proposals)

    def _extract_preferences(self, message: str) -> list[str]:
        preferences: list[str] = []
        for pattern in USER_PREFERENCE_PATTERNS:
            for match in pattern.findall(message):
                normalized = self._normalize_preference(match)
                if normalized:
                    preferences.append(normalized)
        return self._deduplicate_strings(preferences)

    def _extract_interaction_styles(
        self,
        message: str,
        preferences: list[str],
    ) -> list[str]:
        styles = [
            preference
            for preference in preferences
            if self._looks_like_interaction_style(preference)
        ]
        for pattern in INTERACTION_REQUEST_PATTERNS:
            for match in pattern.findall(message):
                normalized = self._normalize_interaction_style(match)
                if normalized:
                    styles.append(normalized)
        return self._deduplicate_strings(styles)

    def _propose_user_preferences(
        self,
        preferences: list[str],
    ) -> list[MemoryUpdateProposal]:
        proposals: list[MemoryUpdateProposal] = []
        for normalized in preferences:
            if self._looks_like_interaction_style(normalized):
                continue
            proposals.append(
                MemoryUpdateProposal(
                    target="user",
                    section="## Preferences",
                    content=normalized,
                    reason="Detected an explicit long-term user preference in the latest turn.",
                    confidence=0.84,
                )
            )
        return proposals

    def _propose_user_projects(self, message: str) -> list[MemoryUpdateProposal]:
        proposals: list[MemoryUpdateProposal] = []
        for pattern in USER_PROJECT_PATTERNS:
            for match in pattern.findall(message):
                normalized = self._normalize_project(match)
                if not normalized:
                    continue
                proposals.append(
                    MemoryUpdateProposal(
                        target="user",
                        section="## Current Projects",
                        content=normalized,
                        reason="Detected current project context that is likely to matter across turns.",
                        confidence=0.76,
                    )
                )
        return proposals

    def _propose_user_interaction_style(
        self,
        interaction_styles: list[str],
    ) -> list[MemoryUpdateProposal]:
        if not interaction_styles:
            return []
        latest_style = interaction_styles[-1]
        return [
            MemoryUpdateProposal(
                target="user",
                section="## Interaction Style",
                content=latest_style,
                reason="The user described a durable collaboration or communication preference.",
                confidence=0.86,
                operation="replace",
                category="interaction_style",
            )
        ]

    def _propose_agent_working_style(
        self,
        interaction_styles: list[str],
    ) -> list[MemoryUpdateProposal]:
        if not interaction_styles:
            return []
        latest_style = interaction_styles[-1]
        description = latest_style
        if latest_style.lower().startswith("prefers "):
            description = latest_style[8:]
        return [
            MemoryUpdateProposal(
                target="agent",
                section="## Working Style",
                content=f"Match the user's preferred collaboration style: {description}",
                reason="A durable user collaboration preference should shape the agent's working style.",
                confidence=0.79,
                operation="replace",
                category="working_style",
            )
        ]

    def _propose_agent_tool_reporting(
        self,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> list[MemoryUpdateProposal]:
        if plan.intent != "tool_use" or not observation.tool_results:
            return []
        if not any(result.success for result in observation.tool_results):
            return []
        return [
            MemoryUpdateProposal(
                target="agent",
                section="## Behavior Principles",
                content="Reference concrete tool outcomes when summarizing tool-assisted work",
                reason="Successful tool use should produce inspectable, explicit reporting.",
                confidence=0.7,
                category="tool_reporting",
            )
        ]

    def _looks_like_interaction_style(self, value: str) -> bool:
        lowered = value.lower()
        return any(keyword in lowered for keyword in INTERACTION_STYLE_KEYWORDS) and any(
            hint in lowered for hint in INTERACTION_STYLE_HINTS
        )

    def _normalize_preference(self, value: str) -> str:
        cleaned = value.strip(" 。！?!\n")
        if not cleaned:
            return ""
        if re.search(r"[\u4e00-\u9fff]", cleaned):
            if cleaned.startswith("偏好"):
                return cleaned
            return f"偏好 {cleaned}".strip()

        lowered = cleaned.lower()
        for prefix in (
            "i prefer ",
            "i prefers ",
            "i like ",
            "i likes ",
            "prefer ",
            "prefers ",
            "like ",
            "likes ",
        ):
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break
        return f"Prefers {cleaned}".strip()

    def _normalize_interaction_style(self, value: str) -> str:
        cleaned = value.strip(" 。！?!\n,")
        if not cleaned:
            return ""
        if re.search(r"[\u4e00-\u9fff]", cleaned):
            cleaned = re.sub(r"^(?:给我|保持|使用|采用)", "", cleaned).strip()
            if cleaned.startswith("偏好"):
                return cleaned
            return f"偏好 {cleaned}".strip()

        lowered = cleaned.lower()
        for prefix in (
            "give me ",
            "keep ",
            "make ",
            "write ",
            "answer with ",
            "respond with ",
            "use ",
        ):
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break
        return f"Prefers {cleaned}".strip()

    def _normalize_project(self, value: str) -> str:
        cleaned = value.strip(" 。！?!\n")
        if not cleaned:
            return ""
        if re.search(r"[\u4e00-\u9fff]", cleaned):
            return cleaned
        cleaned = re.sub(r"^(?:a|an|the)\s+", "", cleaned, flags=re.IGNORECASE)
        return cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()

    def _deduplicate(
        self,
        proposals: list[MemoryUpdateProposal],
    ) -> list[MemoryUpdateProposal]:
        seen: set[tuple[str, str, str, str]] = set()
        unique: list[MemoryUpdateProposal] = []
        for proposal in proposals:
            signature = (
                proposal.target,
                proposal.section,
                proposal.content,
                proposal.operation,
            )
            if signature in seen:
                continue
            seen.add(signature)
            unique.append(proposal)
        return unique

    def _deduplicate_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique
