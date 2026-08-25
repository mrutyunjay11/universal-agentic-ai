# Universal Agentic AI — Specialized Agent Profiles

## 1. Registered Specialized Agents

The system provides 8 standardized agent profiles:

| Agent Name | Primary Role | Core Capabilities | Preferred Tools | Max Permission Tier |
| :--- | :--- | :--- | :--- | :--- |
| `ResearcherAgent` | Web research & literature review | `web.search`, `web.fetch`, `research.compare` | `search_web`, `fetch_web_page` | `NETWORK` |
| `CoderAgent` | Software engineering & implementation | `file.write`, `code.edit`, `code.analyze` | `write_file`, `edit_file`, `analyze_code` | `READ_WRITE` |
| `DebuggerAgent` | Root cause diagnosis & patching | `code.debug`, `code.edit`, `terminal.run` | `analyze_code`, `edit_file`, `verify_code` | `READ_WRITE` |
| `DataAnalystAgent` | Tabular data & statistics | `data.inspect`, `data.statistics`, `math.calculate` | `calculate_statistics`, `calculator` | `READ` |
| `DocumentAnalystAgent` | Document extraction & comparison | `document.extract`, `document.compare`, `file.read` | `read_file`, `list_directory` | `READ` |
| `BrowserAgent` | Dynamic web & DOM extraction | `web.browser`, `web.fetch`, `web.search` | `fetch_web_page`, `search_web` | `NETWORK` |
| `VerifierAgent` | Independent validation & checking | `verify.claim`, `verify.source`, `code.verify` | `verify_claim`, `verify_calculation`, `verify_code` | `READ` |
| `GeneralistAgent` | Fallback autonomous worker | `file.read`, `file.write`, `web.search`, `math.calculate` | `search_web`, `calculator`, `read_file` | `READ_WRITE` |

---

## 2. Standardized Result Contract

Every sub-agent returns a structured `AgentResult`:

```json
{
  "subtask_id": "subtask_101",
  "agent_name": "ResearcherAgent",
  "status": "COMPLETED",
  "summary": "Found official PEP 684 documentation on per-interpreter GIL",
  "artifacts": [{"tool": "search_web", "output": "..."}],
  "evidence": [{"uri": "agent://ResearcherAgent/search_web", "snippet": "..."}],
  "confidence": 0.96,
  "execution_duration_ms": 142
}
```
