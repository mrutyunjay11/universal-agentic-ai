from __future__ import annotations
import pytest
from app.agent.understanding import task_understander
from app.agent.classifier import task_classifier
from app.agent.state import TaskType, RiskLevel


class TestTaskUnderstandingAndClassification:
    def test_understand_research_task(self):
        req = "Search and find out the latest features in Python 3.12 documentation without using third party blogs"
        res = task_understander.understand(req)
        assert res.requires_web_research is True
        assert res.requires_verification is True
        assert len(res.constraints) >= 1
        assert len(res.required_evidence) >= 1
        assert len(res.success_criteria) >= 1

    def test_understand_high_risk_deletion(self):
        req = "Delete all unused temporary files and rm -rf ./tmp"
        res = task_understander.understand(req)
        assert res.risk_level == RiskLevel.HIGH
        assert len(res.potential_risks) >= 1

    def test_classify_coding_task(self):
        req = "Fix the bug in auth service and write a unit test"
        t = task_classifier.classify(req)
        assert t in (TaskType.CODING, TaskType.DEBUGGING)

    def test_classify_math_task(self):
        req = "Calculate the square root of 144 and solve the equation x^2 - 4 = 0"
        t = task_classifier.classify(req)
        assert t in (TaskType.MATHEMATICAL, TaskType.MULTI_DOMAIN)

    def test_classify_multi_domain_task(self):
        req = "Research the official library documentation, write a test in python, and verify compatibility"
        t = task_classifier.classify(req)
        assert t == TaskType.MULTI_DOMAIN
