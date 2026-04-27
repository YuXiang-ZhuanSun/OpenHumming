from uuid import uuid4

from openhumming.agent.executor import Executor
from openhumming.agent.loop import build_system_prompt
from openhumming.agent.observer import Observer
from openhumming.agent.planner import Planner
from openhumming.agent.reflection import Reflection
from openhumming.agent.state import AgentTurnResult
from openhumming.config.settings import Settings
from openhumming.llm.base import ChatMessage, LLMProvider
from openhumming.memory.store import MemoryStore
from openhumming.skills.manager import SkillManager
from openhumming.tools.registry import ToolRegistry
from openhumming.trace.recorder import TraceRecorder


class AgentRuntime:
    def __init__(
        self,
        *,
        settings: Settings,
        memory_store: MemoryStore,
        provider: LLMProvider,
        trace_recorder: TraceRecorder,
        skill_manager: SkillManager,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.settings = settings
        self.memory_store = memory_store
        self.provider = provider
        self.trace_recorder = trace_recorder
        self.skill_manager = skill_manager
        self.planner = Planner()
        self.executor = Executor(tool_registry, trace_recorder)
        self.observer = Observer()
        self.reflection = Reflection()

    def respond(self, session_id: str | None, message: str) -> AgentTurnResult:
        resolved_session_id = session_id or f"session_{uuid4().hex[:8]}"
        context = self.memory_store.load_context(
            history_limit=self.settings.conversation_history_limit,
            session_id=resolved_session_id,
        )
        skills = self.skill_manager.list_skills()
        plan = self.planner.plan(message, skills)
        relevant_skills = self.skill_manager.find_relevant_skills(message, limit=3)

        actions = ["load_profiles", "load_history"]
        if relevant_skills:
            actions.append("load_skills")

        self.trace_recorder.record(
            "turn_started",
            {
                "session_id": resolved_session_id,
                "message": message,
                "intent": plan.intent,
            },
        )

        execution = self.executor.execute(plan)
        actions.extend(execution.actions)
        observation = self.observer.observe(execution)
        reflection = self.reflection.reflect(message, plan, observation)

        system_prompt = build_system_prompt(context, relevant_skills, plan, observation)
        messages = [
            ChatMessage(role=item.role, content=item.content)
            for item in context.conversation_history
        ]
        messages.append(ChatMessage(role="user", content=message))
        response = self.provider.generate(messages, system_prompt=system_prompt)

        self.memory_store.save_turn(
            session_id=resolved_session_id,
            user_message=message,
            assistant_message=response,
            metadata={
                "intent": plan.intent,
                "tool_actions": [result.tool_name for result in execution.tool_results],
            },
        )
        actions.append("record_conversation")

        if reflection.should_consider_skill_creation:
            actions.append("consider_skill_creation")
        if reflection.should_update_user_memory:
            actions.append("consider_user_memory_update")

        self.trace_recorder.record(
            "turn_completed",
            {
                "session_id": resolved_session_id,
                "response_length": len(response),
                "actions": actions,
            },
        )

        return AgentTurnResult(
            session_id=resolved_session_id,
            response=response,
            actions=actions,
            memory_updates={
                "agent": reflection.should_update_agent_memory,
                "user": reflection.should_update_user_memory,
            },
        )
