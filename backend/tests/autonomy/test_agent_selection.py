import pytest
from app.autonomy.agent_pool import AgentPool
from app.agents import (
    researcher_profile,
    coder_profile,
    data_analyst_profile,
    verifier_profile,
)


class TestAgentSelection:
    def test_capability_matching_and_selection(self):
        pool = AgentPool()

        # 1. Research match
        profile_res = pool.select_agent_for_capabilities(["web.search", "web.fetch"])
        assert profile_res.name == "ResearcherAgent"

        # 2. Coding match
        profile_code = pool.select_agent_for_capabilities(["file.write", "code.edit"])
        assert profile_code.name == "CoderAgent"

        # 3. Data analysis match
        profile_data = pool.select_agent_for_capabilities(["data.statistics", "math.calculate"])
        assert profile_data.name == "DataAnalystAgent"

        # 4. Verifier match
        profile_ver = pool.select_agent_for_capabilities(["verify.claim", "verify.source"])
        assert profile_ver.name == "VerifierAgent"
