from uuid import uuid4

from openhumming.agent.executor import Executor
from openhumming.agent.loop import build_system_prompt
from openhumming.agent.observer import Observer
from openhumming.agent.planner import Planner
from openhumming.agent.reflection import Reflection
from openhumming.agent.state import TurnObservation, TurnPlan
from openhumming.agent.state import AgentTurnResult
from openhumming.config.settings import Settings
from openhumming.llm.base import ChatMessage, LLMProvider
from openhumming.memory.applier import MemoryApplier
from openhumming.memory.models import AppliedMemoryUpdate, MemoryUpdateProposal
from openhumming.memory.store import MemoryStore
from openhumming.skills.candidate_evaluator import SkillCandidateEvaluator
from openhumming.skills.extractor import SkillExtractor
from openhumming.skills.manager import SkillManager
from openhumming.skills.workflow_capture import WorkflowCaptureBuilder
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
        self.skill_extractor = SkillExtractor()
        self.skill_candidate_evaluator = SkillCandidateEvaluator()
        self.workflow_capture_builder = WorkflowCaptureBuilder()
        self.planner = Planner()
        self.executor = Executor(tool_registry, trace_recorder)
        self.observer = Observer()
        self.reflection = Reflection()
        self.memory_applier = MemoryApplier(
            agent_profile=self.memory_store.paths.agent_profile,
            user_profile=self.memory_store.paths.user_profile,
        )

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
        artifact_notes: list[str] = []
        applied_memory_updates = self._apply_memory_proposals(reflection.memory_proposals)
        created_skill_draft_payload: dict[str, object] | None = None
        skill_draft_event: str | None = None

        if reflection.memory_proposals:
            actions.append("propose_memory_updates")
        if any(update.target == "agent" for update in applied_memory_updates):
            actions.append("update_agent_memory")
        if any(update.target == "user" for update in applied_memory_updates):
            actions.append("update_user_memory")
        artifact_notes.extend(self._format_memory_update_notes(applied_memory_updates))

        created_skill_draft, skill_draft_event = self._create_skill_draft_from_turn(
            session_id=resolved_session_id,
            message=message,
            response=response,
            plan=plan,
            observation=observation,
        )
        if created_skill_draft is not None:
            actions.append(
                "create_skill_draft" if skill_draft_event == "created" else "update_skill_draft"
            )
            created_skill_draft_payload = {
                "name": created_skill_draft.name,
                "slug": created_skill_draft.slug,
                "description": created_skill_draft.description,
                "path": str(created_skill_draft.path),
                "status": created_skill_draft.status,
                "metadata": created_skill_draft.metadata,
                "event": skill_draft_event or "created",
            }
            artifact_notes.append(
                (
                    f"Created skill draft: {created_skill_draft.name} "
                    f"({created_skill_draft.path.name})"
                )
                if skill_draft_event == "created"
                else (
                    f"Updated skill draft reuse: {created_skill_draft.name} "
                    f"(times_reused={created_skill_draft.metadata.get('times_reused', 0)})"
                )
            )
            self.trace_recorder.record(
                "skill_draft_created" if skill_draft_event == "created" else "skill_draft_updated",
                {
                    "name": created_skill_draft.name,
                    "path": str(created_skill_draft.path),
                    "session_id": resolved_session_id,
                    "event": skill_draft_event or "created",
                },
            )

        self.memory_store.save_turn(
            session_id=resolved_session_id,
            user_message=message,
            assistant_message=self._append_artifact_notes(response, artifact_notes),
            metadata={
                "intent": plan.intent,
                "tool_actions": [result.tool_name for result in execution.tool_results],
                "memory_updates": [
                    {
                        "target": update.target,
                        "section": update.section,
                        "content": update.content,
                        "operation": update.operation,
                        "replaced": update.replaced,
                    }
                    for update in applied_memory_updates
                ],
                "created_skill_draft": created_skill_draft_payload,
            },
        )
        actions.append("record_conversation")

        if observation.tool_results:
            actions.append("evaluate_skill_candidate")
        if reflection.should_consider_skill_creation and "create_skill_draft" not in actions:
            actions.append("consider_skill_creation")

        final_response = self._append_artifact_notes(response, artifact_notes)

        self.trace_recorder.record(
            "turn_completed",
            {
                "session_id": resolved_session_id,
                "response_length": len(final_response),
                "actions": actions,
            },
        )

        return AgentTurnResult(
            session_id=resolved_session_id,
            response=final_response,
            actions=actions,
            memory_updates={
                "agent": any(
                    update.target == "agent" for update in applied_memory_updates
                ),
                "user": any(
                    update.target == "user" for update in applied_memory_updates
                ),
            },
            memory_proposals=reflection.memory_proposals,
            applied_memory_updates=applied_memory_updates,
            created_skill_draft=created_skill_draft_payload,
        )

    def _create_skill_draft_from_turn(
        self,
        *,
        session_id: str,
        message: str,
        response: str,
        plan: TurnPlan,
        observation: TurnObservation,
    ) -> tuple[object | None, str | None]:
        if not observation.tool_results:
            return None, None

        capture = self.workflow_capture_builder.capture(
            session_id=session_id,
            message=message,
            response=response,
            plan=plan,
            observation=observation,
        )
        assessment = self.skill_candidate_evaluator.evaluate(capture)
        self.trace_recorder.record(
            "workflow_evaluated",
            {
                "session_id": session_id,
                "intent": capture.intent,
                "step_count": len(capture.steps),
                "successful_steps": len(capture.successful_steps),
                "should_create_draft": assessment.should_create_draft,
                "reason": assessment.reason,
                "confidence": assessment.confidence,
            },
        )
        if not assessment.should_create_draft:
            return None, None

        draft = self.skill_extractor.draft_from_capture(
            capture=capture,
            confidence=assessment.confidence,
            reason=assessment.reason,
        )
        existing = self.skill_manager.get_skill(draft.name)
        existing_draft = self.skill_manager.get_skill_draft(draft.name)
        if existing is not None or existing_draft is not None:
            if existing_draft is None:
                return None, None
            refreshed_draft = self.skill_manager.refresh_skill_draft(
                existing_draft.slug,
                draft=draft,
            )
            return refreshed_draft, "updated"

        return (
            self.skill_manager.create_skill_draft(
                name=draft.name,
                description=draft.description,
                when_to_use=draft.when_to_use,
                inputs=draft.inputs,
                procedure=draft.procedure,
                output=draft.output,
                metadata=draft.metadata,
            ),
            "created",
        )

    def _append_artifact_notes(
        self,
        response: str,
        artifact_notes: list[str],
    ) -> str:
        if not artifact_notes:
            return response
        return response.rstrip() + "\n\n" + "\n".join(artifact_notes)

    def _apply_memory_proposals(
        self,
        proposals: list[MemoryUpdateProposal],
    ) -> list[AppliedMemoryUpdate]:
        applied = self.memory_applier.apply(proposals)
        for update in applied:
            self.trace_recorder.record(
                "memory_updated",
                {
                    "target": update.target,
                    "section": update.section,
                    "content": update.content,
                    "path": str(update.path),
                    "operation": update.operation,
                    "replaced": update.replaced,
                },
            )
        return applied

    def _format_memory_update_notes(
        self,
        updates: list[AppliedMemoryUpdate],
    ) -> list[str]:
        notes: list[str] = []
        for update in updates:
            if update.operation == "replace" and update.replaced:
                notes.append(
                    f"Updated {update.target} memory: {update.section} -> "
                    f"{update.replaced} => {update.content}"
                )
                continue
            notes.append(
                f"Updated {update.target} memory: {update.section} -> {update.content}"
            )
        return notes
