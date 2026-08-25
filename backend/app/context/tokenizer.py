from __future__ import annotations
import math
from typing import Any, Optional


class TokenizerProvider:
    """
    Model-aware tokenizer abstraction.
    Uses exact tokenization where available (e.g. tiktoken/model BPE),
    falling back to conservative language-aware estimation when offline,
    with explicit approximation status metadata.
    """

    def __init__(self):
        self._tiktoken_available = False
        try:
            import tiktoken
            self._tiktoken = tiktoken
            self._tiktoken_available = True
        except ImportError:
            self._tiktoken = None

    def count_tokens(self, text: str, model: str = "default") -> tuple[int, bool]:
        """
        Returns (token_count, is_exact).
        """
        if not text:
            return 0, True

        if self._tiktoken_available and self._tiktoken:
            try:
                # Try resolving encoding for OpenAI-compatible or cl100k_base
                encoding = self._tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(text)
                return len(tokens), True
            except Exception:
                pass

        # Conservative model-aware estimation:
        # Code and dense technical text have higher token/char ratios than prose.
        # Average English: ~4 chars/token. Technical/JSON/Code: ~3.2 chars/token.
        chars = len(text)
        is_technical = any(ch in text for ch in "{}[]()<>=:;/\\_`\"")
        ratio = 3.2 if is_technical else 3.8
        estimated = max(1, math.ceil(chars / ratio))
        return estimated, False

    def truncate_to_budget(self, text: str, max_tokens: int, model: str = "default") -> str:
        """
        Truncates text to safely fit within max_tokens without breaking sentences when possible.
        """
        if max_tokens <= 0:
            return ""

        count, is_exact = self.count_tokens(text, model)
        if count <= max_tokens:
            return text

        # If exact tokenizer available
        if self._tiktoken_available and self._tiktoken:
            try:
                encoding = self._tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(text)
                if len(tokens) > max_tokens:
                    return encoding.decode(tokens[:max_tokens])
            except Exception:
                pass

        # Fallback conservative truncation
        ratio = 3.2
        target_chars = int(max_tokens * ratio)
        truncated = text[:target_chars]
        last_space = truncated.rfind(" ")
        if last_space > target_chars * 0.8:
            truncated = truncated[:last_space]
        return truncated + "..."


tokenizer_provider = TokenizerProvider()
