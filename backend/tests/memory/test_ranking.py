import pytest
from app.memory.ranking import MemoryRanker, RankingWeights
from app.memory.models import MemoryRecord, MemoryType, VerificationStatus, FreshnessStatus


class TestMemoryRanking:
    def test_ranking_weights_and_scores(self):
        ranker = MemoryRanker()

        verified_rec = MemoryRecord(
            id="rec_1",
            content="Official API documentation: endpoint accepts JSON POST",
            importance=0.9,
            confidence=0.95,
            verification_status=VerificationStatus.VERIFIED,
            freshness_status=FreshnessStatus.CURRENT,
        )

        unverified_rec = MemoryRecord(
            id="rec_2",
            content="Random blog post: endpoint accepts XML",
            importance=0.4,
            confidence=0.5,
            verification_status=VerificationStatus.UNVERIFIED,
            freshness_status=FreshnessStatus.CURRENT,
        )

        stale_rec = MemoryRecord(
            id="rec_3",
            content="Deprecated endpoint accepts GET",
            importance=0.5,
            confidence=0.8,
            verification_status=VerificationStatus.SUPERSEDED,
            freshness_status=FreshnessStatus.SUPERSEDED,
        )

        ranked = ranker.rank(
            query="endpoint accepts",
            records=[unverified_rec, stale_rec, verified_rec],
            semantic_scores={"rec_1": 0.8, "rec_2": 0.6, "rec_3": 0.5},
        )

        assert len(ranked) == 3
        # Verified record must rank first
        assert ranked[0][1].id == "rec_1"
        assert ranked[0][0] > ranked[1][0]
        # Superseded record must receive penalty and rank last
        assert ranked[2][1].id == "rec_3"
