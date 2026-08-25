from __future__ import annotations
import re
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.planner import ContextPlan


class SubQuery(BaseModel):
    query_text: str
    target_aspect: str
    priority: int = 5
    requirement_id: Optional[str] = None


class QueryDecomposer:
    """
    Decomposes complex, multi-hop user tasks into bounded sub-queries.
    Applies guardrails against combinatorial query explosions and removes duplicate searches.
    """

    def __init__(self, max_subqueries: int = 5, max_query_length: int = 200):
        self.max_subqueries = max_subqueries
        self.max_query_length = max_query_length

    def decompose(self, plan: ContextPlan) -> list[SubQuery]:
        subqueries: list[SubQuery] = []
        seen_texts: set[str] = set()

        for req in plan.required_information:
            # Generate focused sub-query based on requirement
            clean_desc = req.description[:self.max_query_length]
            q_text = f"{plan.task} {clean_desc}"
            # Normalize whitespace
            q_norm = " ".join(q_text.split()).lower()

            if q_norm in seen_texts:
                continue
            seen_texts.add(q_norm)

            subqueries.append(SubQuery(
                query_text=clean_desc,
                target_aspect=req.requirement_type,
                priority=8 if req.is_mandatory else 5,
                requirement_id=req.id,
            ))

            if len(subqueries) >= self.max_subqueries:
                break

        if not subqueries:
            subqueries.append(SubQuery(query_text=plan.task[:self.max_query_length], target_aspect="GENERAL"))

        return subqueries


query_decomposer = QueryDecomposer()
