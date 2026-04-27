from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openhumming.agent.runtime import AgentRuntime

__all__ = ["AgentRuntime"]


def __getattr__(name: str):
    if name == "AgentRuntime":
        from openhumming.agent.runtime import AgentRuntime

        return AgentRuntime
    raise AttributeError(name)
