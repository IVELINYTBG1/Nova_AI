from __future__ import annotations

from nova.agents.base_agent import BaseAgent
from nova.core.result_types import AgentMetadata


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.metadata.name] = agent

    def get(self, name: str) -> BaseAgent:
        return self._agents[name]

    def list_metadata(self) -> list[AgentMetadata]:
        return [agent.metadata for agent in self._agents.values()]