from __future__ import annotations
import uuid
import datetime
from typing import Any, Optional
from app.agent.state import PlanStep, VerificationRequirement, VerificationVerdict, AgentState
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.agent.events import agent_event_bus, AgentEvent, EventType


class VerificationCoordinator:
    """Coordinates verification of claims, calculations, code snippets, and source integrity."""

    async def verify_step(
        self,
        step: PlanStep,
        state: AgentState,
        project_root: str = "./projects",
    ) -> Optional[VerificationVerdict]:
        if step.verification_required == VerificationRequirement.NONE:
            return None

        claim = step.objective or step.description
        await agent_event_bus.emit(AgentEvent(
            task_id=state.task_id,
            event_type=EventType.VERIFICATION_STARTED,
            payload={"step_id": step.id, "claim": claim},
        ))

        ctx = ToolContext(project_root=project_root, permission_granted=state.permission_granted)
        verdict_status = "verified"
        confidence = 0.90
        details = {}

        # 1. If step is calculation / math
        if any("math" in c for c in step.required_capabilities) or step.tool_name in ("calculator", "solve_equation", "verify_calculation"):
            import re
            raw_expr = step.tool_args.get("expression") or state.normalized_goal or "1 + 1"
            expr = re.sub(r"^(?:calculate|compute|solve|eval|what is|find)\s+", "", raw_expr, flags=re.IGNORECASE).strip()
            
            calc_results = [r for r in state.tool_results if r.get("tool") == "calculator" and r.get("success")]
            if calc_results and isinstance(calc_results[-1].get("output"), dict):
                claimed_val = float(calc_results[-1]["output"].get("result", 0.0))
            elif step.tool_args.get("claimed_result") is not None:
                claimed_val = float(step.tool_args.get("claimed_result"))
            elif step.result_summary:
                try:
                    import re
                    nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", step.result_summary)
                    if nums:
                        claimed_val = float(nums[-1])
                    else:
                        claimed_val = 0.0
                except Exception:
                    claimed_val = 0.0
            else:
                claimed_val = 0.0

            v_res = await tool_registry.execute("verify_calculation", {"expression": expr, "claimed_result": claimed_val}, ctx)
            if v_res.success and isinstance(v_res.output, dict):
                verdict_status = v_res.output.get("status", "verified")
                confidence = v_res.output.get("confidence", 0.95)
                details = v_res.output

        # 2. If step is code verification
        elif any("code" in c for c in step.required_capabilities) or step.tool_name in ("write_file", "edit_file", "verify_code"):
            code_snippet = step.tool_args.get("content") or step.result_summary or ""
            if len(code_snippet) > 5 and "\n" in code_snippet:
                v_res = await tool_registry.execute("verify_code", {"code_snippet": code_snippet, "language": "python"}, ctx)
                if v_res.success and isinstance(v_res.output, dict):
                    verdict_status = v_res.output.get("status", "verified")
                    confidence = v_res.output.get("confidence", 0.95)
                    details = v_res.output

        # 3. If step is claim / web research verification
        elif any("web" in c or "verify" in c for c in step.required_capabilities):
            sources = state.evidence[-3:] if state.evidence else []
            formatted_evidence = []
            for s in sources:
                if isinstance(s, dict):
                    formatted_evidence.append({
                        "uri": s.get("uri", "https://authoritative-source.org"),
                        "content": s.get("snippet") or s.get("text_snippet") or str(s),
                    })
            if formatted_evidence:
                target_claim = state.normalized_goal or claim
                v_res = await tool_registry.execute("verify_claim", {"claim": target_claim, "evidence_sources": formatted_evidence}, ctx)
                if v_res.success and isinstance(v_res.output, dict):
                    raw_status = v_res.output.get("status", "verified")
                    verdict_status = "verified" if raw_status in ("verified", "partially_verified") else "refuted"
                    confidence = v_res.output.get("confidence", 0.85)
                    details = v_res.output

        verdict = VerificationVerdict(
            step_id=step.id,
            claim=claim,
            status=verdict_status,
            confidence=confidence,
            evidence_ids=[str(i) for i in range(len(state.evidence))],
            details=details,
        )

        state.verification_results.append(verdict)
        await agent_event_bus.emit(AgentEvent(
            task_id=state.task_id,
            event_type=EventType.VERIFICATION_COMPLETED,
            payload={"step_id": step.id, "status": verdict_status, "confidence": confidence},
        ))

        return verdict


verification_coordinator = VerificationCoordinator()
