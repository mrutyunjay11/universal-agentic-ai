import pytest
from app.context.tokenizer import TokenizerProvider


class TestTokenizer:
    def test_token_counting_and_truncation(self):
        tp = TokenizerProvider()
        text = "Universal Agentic AI dynamic context working reasoning surface."

        count, is_exact = tp.count_tokens(text)
        assert count > 0
        assert isinstance(is_exact, bool)

        # Truncation test
        truncated = tp.truncate_to_budget(text, max_tokens=3)
        assert len(truncated) < len(text)
