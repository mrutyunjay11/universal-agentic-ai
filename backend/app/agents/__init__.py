from app.agents.base import BaseSpecializedAgent, AgentResult
from app.agents.profiles.researcher import researcher_profile
from app.agents.profiles.coder import coder_profile
from app.agents.profiles.debugger import debugger_profile
from app.agents.profiles.data_analyst import data_analyst_profile
from app.agents.profiles.document_analyst import document_analyst_profile
from app.agents.profiles.browser_agent import browser_agent_profile
from app.agents.profiles.verifier import verifier_profile
from app.agents.profiles.generalist import generalist_profile

ALL_AGENT_PROFILES = [
    researcher_profile,
    coder_profile,
    debugger_profile,
    data_analyst_profile,
    document_analyst_profile,
    browser_agent_profile,
    verifier_profile,
    generalist_profile,
]

__all__ = [
    "BaseSpecializedAgent",
    "AgentResult",
    "researcher_profile",
    "coder_profile",
    "debugger_profile",
    "data_analyst_profile",
    "document_analyst_profile",
    "browser_agent_profile",
    "verifier_profile",
    "generalist_profile",
    "ALL_AGENT_PROFILES",
]
