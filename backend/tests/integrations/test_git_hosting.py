import pytest
from app.integrations.connectors.github import github_connector
from app.integrations.connectors.gitlab import gitlab_connector
from app.integrations.base import IntegrationContext


class TestGitHosting:
    @pytest.mark.asyncio
    async def test_github_pull_request_and_review(self):
        ctx = IntegrationContext()
        res = await github_connector.execute("create_pull_request", ctx, title="New Feature")
        assert res.status == "SUCCESS"
        assert res.data["pr_number"] == 42

        review = await github_connector.execute("review_pull_request", ctx, pr_number=42)
        assert review.status == "SUCCESS"
        assert review.data["review_status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_gitlab_pipeline_trigger(self):
        ctx = IntegrationContext()
        res = await gitlab_connector.execute("trigger_pipeline", ctx, project_id="554")
        assert res.status == "SUCCESS"
        assert "gitlab_action" in res.data
