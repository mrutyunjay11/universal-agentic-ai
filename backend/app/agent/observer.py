from __future__ import annotations
import uuid
import datetime
from typing import Any, Optional
from app.agent.state import StructuredObservation, AgentState, PlanStep
from app.agent.executor import StepExecutionResult
from app.agent.events import agent_event_bus, AgentEvent, EventType


class ObservationManager:
    """Transforms raw tool outputs into structured, evidence-bearing observations without blowing up context window limits."""

    def observe(
        self,
        step: PlanStep,
        result: StepExecutionResult,
        state: AgentState,
    ) -> StructuredObservation:
        evidence: list[dict[str, Any]] = []
        reliability = 1.0

        # Summarize output
        if result.success:
            if isinstance(result.output, dict):
                # Check for evidence fields
                if "results" in result.output and isinstance(result.output["results"], list):
                    for item in result.output["results"][:5]:
                        if isinstance(item, dict):
                            evidence.append({
                                "uri": item.get("url") or item.get("uri") or "",
                                "title": item.get("title") or "",
                                "snippet": item.get("snippet") or item.get("content") or "",
                            })
                elif "files" in result.output:
                    evidence.append({"type": "file_list", "count": len(result.output["files"])})
                elif "computed_result" in result.output:
                    evidence.append({
                        "expression": result.output.get("expression"),
                        "value": result.output.get("computed_result"),
                    })

                summary = f"Tool '{result.tool_name}' completed successfully. Output summary: {str(result.output)[:400]}"
            elif isinstance(result.output, str):
                summary = f"Tool '{result.tool_name}' returned: {result.output[:300]}"
                evidence.append({"text_snippet": result.output[:300]})
            else:
                summary = f"Tool '{result.tool_name}' returned result: {str(result.output)[:200]}"
        else:
            summary = f"Tool '{result.tool_name}' failed with error: {result.error}"
            reliability = 0.0

        if result.provenance:
            evidence.append({"provenance": result.provenance})

        obs = StructuredObservation(
            id=f"obs_{uuid.uuid4().hex[:8]}",
            step_id=step.id,
            tool_name=result.tool_name,
            summary=summary,
            raw_reference_id=f"raw_{result.step_id}_{int(datetime.datetime.now().timestamp())}",
            success=result.success,
            evidence=evidence,
            reliability=reliability,
            duration_ms=result.duration_ms,
        )

        state.observations.append(obs)
        if evidence:
            state.evidence.extend(evidence)

        return obs


observation_manager = ObservationManager()
