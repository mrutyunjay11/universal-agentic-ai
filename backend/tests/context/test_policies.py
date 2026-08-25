import pytest
from app.context.policies import (
    ContextStrategy,
    ContextSufficiencyStatus,
    ContradictionType,
    ProgressiveLevel,
    ContextSlotType,
    OrderingStrategy,
)


class TestContextPolicies:
    def test_enum_definitions_and_values(self):
        assert ContextStrategy.ITERATIVE_RAG.value == "ITERATIVE_RAG"
        assert ContextStrategy.HIERARCHICAL_RETRIEVAL.value == "HIERARCHICAL_RETRIEVAL"
        assert ContextSufficiencyStatus.SUFFICIENT.value == "SUFFICIENT"
        assert ContradictionType.VERSION_DIFFERENCE.value == "VERSION_DIFFERENCE"
        assert ProgressiveLevel.METADATA.value == 0
        assert ProgressiveLevel.FULL_DOC.value == 4
        assert ContextSlotType.PRIMARY_EVIDENCE.value == "PRIMARY_EVIDENCE"
        assert OrderingStrategy.POSITION_AWARE.value == "POSITION_AWARE"
