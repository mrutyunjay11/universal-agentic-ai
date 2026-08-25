from __future__ import annotations
from typing import Any, Optional
from app.autonomy.task_graph import TaskGraph, SubTaskStatus
from app.agents.base import AgentResult


class ResultAggregator:
    """
    Aggregates subtask execution results, shared artifacts, collected evidence,
    and verification outputs into a single coherent master task result.
    """

    def aggregate(
        self,
        master_task_id: str,
        goal: str,
        task_graph: TaskGraph,
        agent_results: list[AgentResult],
    ) -> dict[str, Any]:
        combined_summaries: list[str] = []
        all_artifacts: list[dict[str, Any]] = []
        all_evidence: list[dict[str, Any]] = []
        all_errors: list[str] = []
        all_warnings: list[str] = []

        total_confidence = 0.0

        for r in agent_results:
            if r.summary:
                combined_summaries.append(r.summary)
            all_artifacts.extend(r.artifacts)
            all_evidence.extend(r.evidence)
            all_errors.extend(r.errors)
            all_warnings.extend(r.warnings)
            total_confidence += r.confidence

        avg_confidence = (total_confidence / len(agent_results)) if agent_results else 0.80

        # Master status
        has_failed = any(s.status == SubTaskStatus.FAILED for s in task_graph.nodes.values())
        overall_status = "FAILED" if has_failed else "COMPLETED"

        master_summary = f"Multi-agent workflow completed for goal '{goal}'. " + " | ".join(combined_summaries)

        return {
            "master_task_id": master_task_id,
            "goal": goal,
            "status": overall_status,
            "summary": master_summary,
            "total_subtasks": len(task_graph.nodes),
            "completed_subtasks": sum(1 for s in task_graph.nodes.values() if s.status == SubTaskStatus.COMPLETED),
            "artifacts_count": len(all_artifacts),
            "evidence_count": len(all_evidence),
            "artifacts": all_artifacts,
            "evidence": all_evidence,
            "errors": all_errors,
            "warnings": all_warnings,
            "average_confidence": round(avg_confidence, 4),
        }


result_aggregator = ResultAggregator()
