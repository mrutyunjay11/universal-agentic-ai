from __future__ import annotations
import re
from typing import Any, Optional
from app.agent.state import TaskType


class TaskClassifier:
    """Classifies incoming user tasks into standard categories using deterministic heuristics and semantic patterns."""

    def classify(self, request: str, context: Optional[dict[str, Any]] = None) -> TaskType:
        req = request.lower().strip()

        # Multi-domain indicators
        has_fact_check = any(k in req for k in ("fact-check", "is it true that", "verify claim", "contradiction", "check whether", "compatible with", "verify compatibility"))
        has_research = any(k in req for k in ("search", "research", "find out", "check documentation", "browse"))
        has_coding = any(k in req for k in ("write code", "implement", "create function", "fix bug", "refactor", "unit test", "write script", "debug", "run test", "write a test", "test in python", "coding"))
        has_data = any(k in req for k in ("csv", "dataset", "dataframe", "columns", "calculate statistics"))
        has_math = any(k in req for k in ("calculate", "solve equation", "matrix", "integral", "convert unit", "sqrt("))
        has_browser = any(k in req for k in ("open browser", "click element", "fill form", "browser screenshot", "puppeteer", "playwright"))
        has_doc = any(k in req for k in ("pdf document", "docx document", "summarize doc", "extract table from doc"))
        has_system = any(k in req for k in ("system info", "cpu info", "memory info", "gpu info", "disk usage", "os info"))

        if has_fact_check and not has_coding:
            return TaskType.FACT_CHECK

        domains_detected = sum([has_research, has_coding, has_data, has_math, has_browser, has_doc, has_system])
        if domains_detected >= 2:
            return TaskType.MULTI_DOMAIN

        if has_fact_check:
            return TaskType.FACT_CHECK

        if has_coding:
            if any(k in req for k in ("debug", "error", "traceback", "fix", "exception", "broken", "failing")):
                return TaskType.DEBUGGING
            return TaskType.CODING

        if has_research:
            return TaskType.RESEARCH

        if has_data:
            return TaskType.DATA_ANALYSIS

        if has_math:
            return TaskType.MATHEMATICAL

        if has_browser:
            return TaskType.BROWSER_TASK

        if has_doc:
            return TaskType.DOCUMENT_ANALYSIS

        if has_system:
            return TaskType.SYSTEM_TASK

        # General questions vs unknown
        if any(req.startswith(w) for w in ("what", "how", "why", "who", "when", "where", "explain", "describe", "tell me")):
            return TaskType.GENERAL_QUESTION

        return TaskType.UNKNOWN


task_classifier = TaskClassifier()
