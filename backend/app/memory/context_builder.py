from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from app.memory.models import MemoryRecord, MemoryType
from app.memory.summarization import context_summarizer
from app.agent.state import AgentState, StepStatus


@dataclass
class ContextBudget:
    """Token budget quotas per context layer."""
    max_total_tokens: int = 16000
    system_tokens: int = 2000
    task_tokens: int = 1500
    plan_tokens: int = 1500
    working_memory_tokens: int = 2000
    project_memory_tokens: int = 2000
    external_knowledge_tokens: int = 2500
    evidence_tokens: int = 2500
    tool_result_tokens: int = 2000


@dataclass
class ContextSlot:
    name: str
    content: str
    tokens: int
    provenance_sources: list[str] = field(default_factory=list)


class HierarchicalContextBuilder:
    """
    Builds structured, budgeted LLM prompts by assembling layered context slots.
    Automatically applies compression (truncation, summarization, deduplication) when quotas are exceeded.
    """

    def __init__(self, budget: Optional[ContextBudget] = None):
        self.budget = budget or ContextBudget()

    def build_prompt_context(
        self,
        state: AgentState,
        retrieved_memories: Optional[list[tuple[float, MemoryRecord]]] = None,
        system_instruction: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Assembles all context slots into a final prompt payload with token budgets and provenance.
        """
        slots: list[ContextSlot] = []
        all_memories = [rec for _, rec in (retrieved_memories or [])]

        # 1. SYSTEM SLOT
        sys_text = system_instruction or "You are a universal, goal-driven Agentic AI capable of verifiable tool reasoning."
        slots.append(self._make_slot("SYSTEM", sys_text, self.budget.system_tokens))

        # 2. CURRENT_TASK SLOT
        understanding = state.context.get("understanding", {}) if isinstance(state.context, dict) else {}
        risk_val = getattr(state, "risk_level", None) or understanding.get("risk_level", "LOW")
        if hasattr(risk_val, "value"):
            risk_val = risk_val.value
        crit_list = getattr(state, "success_criteria", None) or understanding.get("success_criteria", [])
        crit_str = ", ".join(crit_list) if crit_list else "Satisfy objective"
        task_text = f"Goal: {state.normalized_goal or state.original_request}\nRisk: {risk_val}\nSuccess Criteria: {crit_str}"
        slots.append(self._make_slot("CURRENT_TASK", task_text, self.budget.task_tokens))

        # 3. CURRENT_PLAN SLOT
        if state.plan:
            plan_lines = [f"- Step {s.id} [{s.status.value}]: {s.tool_name} -> {s.description}" for s in state.plan.steps]
            plan_text = f"Execution Plan (v{state.plan.version}):\n" + "\n".join(plan_lines)
            slots.append(self._make_slot("CURRENT_PLAN", plan_text, self.budget.plan_tokens))

        # 4. RELEVANT_PROJECT_MEMORY
        proj_mems = [m for m in all_memories if m.memory_type == MemoryType.PROJECT]
        if proj_mems:
            proj_text = "\n".join(f"- {m.content}" for m in proj_mems)
            proj_sources = [m.id for m in proj_mems]
            slots.append(self._make_slot("PROJECT_MEMORY", proj_text, self.budget.project_memory_tokens, proj_sources))

        # 5. RELEVANT_FACTS_AND_PROCEDURES
        fact_mems = [m for m in all_memories if m.memory_type in (MemoryType.FACT, MemoryType.PROCEDURAL, MemoryType.SEMANTIC)]
        if fact_mems:
            fact_text = "\n".join(f"- [{m.memory_type.value}] {m.content}" for m in fact_mems)
            fact_sources = [m.id for m in fact_mems]
            slots.append(self._make_slot("EXTERNAL_KNOWLEDGE", fact_text, self.budget.external_knowledge_tokens, fact_sources))

        # 6. EVIDENCE & VERIFICATION
        if state.evidence:
            ev_lines = []
            ev_sources = []
            for ev in state.evidence[-5:]:
                ev_lines.append(f"- Source [{ev.get('uri')}]: {ev.get('snippet', '')[:200]}")
                if "uri" in ev:
                    ev_sources.append(ev["uri"])
            slots.append(self._make_slot("EVIDENCE", "\n".join(ev_lines), self.budget.evidence_tokens, ev_sources))

        # 7. TOOL_RESULTS & RECENT OBSERVATIONS
        if state.observations:
            obs_lines = []
            for obs in state.observations[-4:]:
                summary_snippet = context_summarizer.compress_tool_output(obs.summary, max_chars=300)
                obs_lines.append(f"[{obs.tool_name}]: {summary_snippet}")
            slots.append(self._make_slot("TOOL_RESULTS", "\n".join(obs_lines), self.budget.tool_result_tokens))

        # Assemble full text
        assembled_sections = []
        total_tokens = 0
        provenance_map: dict[str, list[str]] = {}

        for slot in slots:
            assembled_sections.append(f"=== {slot.name} ===\n{slot.content}\n")
            total_tokens += slot.tokens
            if slot.provenance_sources:
                provenance_map[slot.name] = slot.provenance_sources

        return {
            "assembled_prompt": "\n".join(assembled_sections).strip(),
            "total_tokens": total_tokens,
            "slots": {s.name: {"content": s.content, "tokens": s.tokens} for s in slots},
            "provenance_map": provenance_map,
        }

    def _make_slot(self, name: str, content: str, max_tokens: int, sources: Optional[list[str]] = None) -> ContextSlot:
        # Approximate 1 token ~= 4 chars
        max_chars = max_tokens * 4
        if len(content) > max_chars:
            compressed = context_summarizer.compress_tool_output(content, max_chars=max_chars)
        else:
            compressed = content

        est_tokens = max(1, len(compressed) // 4)
        return ContextSlot(name=name, content=compressed, tokens=est_tokens, provenance_sources=sources or [])


context_builder = HierarchicalContextBuilder()
