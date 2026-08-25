from __future__ import annotations
from typing import Any, Optional
from app.autonomy.agent_profile import AgentProfile, AgentStateEnum
from app.agents.base import BaseSpecializedAgent
from app.agents import ALL_AGENT_PROFILES, generalist_profile


class AgentPool:
    """
    Manages active specialized sub-agents. Matches required capabilities against agent profiles
    using capability matching, reliability metrics, and dynamically spawns temporary workers.
    """

    def __init__(self):
        self._profiles: dict[str, AgentProfile] = {p.name: p for p in ALL_AGENT_PROFILES}
        self._active_agents: dict[str, BaseSpecializedAgent] = {}

    def register_profile(self, profile: AgentProfile) -> None:
        self._profiles[profile.name] = profile

    def get_profile(self, profile_name: str) -> Optional[AgentProfile]:
        return self._profiles.get(profile_name)

    def list_profiles(self) -> list[AgentProfile]:
        return list(self._profiles.values())

    def select_agent_for_capabilities(
        self,
        required_capabilities: list[str],
        preferred_tools: Optional[list[str]] = None,
    ) -> AgentProfile:
        """Selects best matching agent profile for a set of required capabilities."""
        best_profile: AgentProfile = generalist_profile
        best_score = -1.0

        for profile in self._profiles.values():
            match_score = profile.matches_capabilities(required_capabilities)
            # Bonus if preferred tools match
            if preferred_tools:
                tool_overlap = sum(1 for t in preferred_tools if t in profile.preferred_tools)
                match_score += (tool_overlap / len(preferred_tools)) * 0.3

            # Factor in reliability
            final_score = match_score * 0.7 + profile.reliability_rating * 0.3

            if final_score > best_score:
                best_score = final_score
                best_profile = profile

        return best_profile

    def get_or_spawn_agent(self, profile_name: str) -> BaseSpecializedAgent:
        """Retrieves or dynamically instantiates an agent worker for a profile."""
        profile = self._profiles.get(profile_name, generalist_profile)
        if profile.name not in self._active_agents:
            self._active_agents[profile.name] = BaseSpecializedAgent(profile)
        return self._active_agents[profile.name]


agent_pool = AgentPool()
