from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExecutionMode(str, Enum):
    SINGLE_AGENT = "SINGLE_AGENT"
    PARALLEL_SUBTASKS = "PARALLEL_SUBTASKS"
    SPECIALIZED_MULTI_AGENT = "SPECIALIZED_MULTI_AGENT"
    HIERARCHICAL_MULTI_AGENT = "HIERARCHICAL_MULTI_AGENT"


@dataclass
class DelegationPolicy:
    """Policies governing multi-agent task delegation and recursion limits."""
    max_delegation_depth: int = 2
    max_subagents: int = 8
    max_parallel_agents: int = 4
    max_total_tasks: int = 20
    max_retries_per_subtask: int = 2
    subtask_timeout_seconds: float = 120.0
    require_independent_verification: bool = True
    enforce_least_privilege: bool = True


@dataclass
class ConsensusStrategy(str, Enum):
    EVIDENCE_FIRST = "EVIDENCE_FIRST"
    VERIFIER_FIRST = "VERIFIER_FIRST"
    SOURCE_AUTHORITY = "SOURCE_AUTHORITY"
    WEIGHTED_AGENT_RELIABILITY = "WEIGHTED_AGENT_RELIABILITY"
    MAJORITY = "MAJORITY"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


default_delegation_policy = DelegationPolicy()
