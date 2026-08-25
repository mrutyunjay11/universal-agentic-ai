import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryRecord, MemoryType, VerificationStatus, FreshnessStatus


class TestMemoryRetrievalAndRanking:
    @pytest.mark.asyncio
    async def test_hybrid_retrieval_and_filtering(self):
        manager = MemoryManager()
        await manager.initialize()

        # Insert test memories
        await manager.remember(
            content="Project uses uv package manager and Python 3.12",
            memory_type=MemoryType.PROJECT,
            project_id="proj_alpha",
            confidence=0.95,
            importance=0.9,
            verification_status=VerificationStatus.VERIFIED,
        )

        await manager.remember(
            content="User prefers pytest over unittest",
            memory_type=MemoryType.USER_PREFERENCE,
            user_id="user_123",
            confidence=0.9,
            importance=0.8,
            verification_status=VerificationStatus.SUPPORTED,
        )

        await manager.remember(
            content="Legacy Node 14 installation procedure",
            memory_type=MemoryType.PROCEDURAL,
            confidence=0.3,
            importance=0.2,
            verification_status=VerificationStatus.SUPERSEDED,
        )

        # 1. Search for project context
        results = await manager.retrieve(query="What python version and package manager?", project_id="proj_alpha")
        assert len(results) >= 1
        top_score, top_rec = results[0]
        assert "uv package manager" in top_rec.content
        assert top_score > 0.4

        # 2. Search for user preference
        user_results = await manager.retrieve(query="test runner preferences", user_id="user_123")
        assert len(user_results) >= 1
        assert "pytest over unittest" in user_results[0][1].content

        # 3. Superseded / low confidence memory should not top the results
        legacy_res = await manager.retrieve(query="installation procedure", min_score=0.4)
        assert not any(rec.verification_status == VerificationStatus.SUPERSEDED for _, rec in legacy_res)
