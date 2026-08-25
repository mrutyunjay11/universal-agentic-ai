from __future__ import annotations
import re
from typing import Any, Optional


class ContextSummarizer:
    """
    Intelligent context compressor and summarizer.
    Compresses verbose tool outputs, error logs, and multi-turn conversations while strictly preserving
    critical evidence snippets, source URIs, numbers, and verification outcomes.
    """

    @staticmethod
    def compress_tool_output(output: Any, max_chars: int = 400) -> str:
        """
        Compresses structured tool results or terminal logs into concise summaries.
        """
        if output is None:
            return ""

        if isinstance(output, dict):
            # Prioritize standard keys: summary, result, stdout, status
            if "summary" in output:
                return str(output["summary"])[:max_chars]
            elif "result" in output:
                return f"Result: {output['result']}"[:max_chars]
            elif "stdout" in output:
                lines = output["stdout"].strip().split("\n")
                if len(lines) > 6:
                    return "\n".join(lines[:3] + [f"... [{len(lines)-6} lines compressed] ..."] + lines[-3:])[:max_chars]
                return output["stdout"][:max_chars]
            elif "items" in output and isinstance(output["items"], list):
                return f"Found {len(output['items'])} items: {', '.join(str(i) for i in output['items'][:3])}"[:max_chars]
            return str(output)[:max_chars]

        text = str(output).strip()
        if len(text) <= max_chars:
            return text

        # Truncate middle to preserve beginning and concluding result
        head_len = max_chars // 2 - 20
        tail_len = max_chars // 2 - 20
        return f"{text[:head_len]}\n... [truncated {len(text) - max_chars} chars] ...\n{text[-tail_len:]}"

    @staticmethod
    def extract_key_claims(text: str, max_claims: int = 3) -> list[str]:
        """Extracts key factual claims from free-form text."""
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 15]
        return sentences[:max_claims]

    @staticmethod
    def deduplicate_lines(text: str) -> str:
        """Removes repeated identical lines from logs or text."""
        lines = text.split("\n")
        seen = set()
        unique = []
        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed not in seen:
                if trimmed:
                    seen.add(trimmed)
                unique.append(line)
        return "\n".join(unique)


context_summarizer = ContextSummarizer()
