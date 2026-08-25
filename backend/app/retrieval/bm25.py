from __future__ import annotations
import math
import re
from typing import Any, Optional
from app.retrieval.candidate import RetrievalCandidate


class BM25Retriever:
    """
    Deterministic BM25 & Lexical Exact Matching Engine.
    Specialized for technical identifiers, error codes, version tags, file paths, and function symbols.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[RetrievalCandidate] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.num_docs: int = 0

    def index_documents(self, documents: list[RetrievalCandidate]) -> None:
        self.corpus = list(documents)
        self.num_docs = len(documents)
        self.doc_lengths = []
        self.doc_freqs = {}

        total_length = 0
        for doc in self.corpus:
            tokens = self._tokenize(doc.content)
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_length = total_length / max(1, self.num_docs)

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"[\w\.\:\-\_\/]+", text) if w.strip()]

    def search(self, query: str, top_k: int = 50) -> list[RetrievalCandidate]:
        if not self.corpus or not query:
            return []

        query_tokens = self._tokenize(query)
        scores: list[tuple[int, float]] = []

        for idx, doc in enumerate(self.corpus):
            doc_tokens = self._tokenize(doc.content)
            doc_len = self.doc_lengths[idx]
            score = 0.0

            # 1. BM25 calculation
            tf_dict: dict[str, int] = {}
            for t in doc_tokens:
                tf_dict[t] = tf_dict.get(t, 0) + 1

            for q_tok in query_tokens:
                if q_tok in tf_dict:
                    tf = tf_dict[q_tok]
                    df = self.doc_freqs.get(q_tok, 0)
                    idf = math.log(1 + (self.num_docs - df + 0.5) / (df + 0.5))
                    num = tf * (self.k1 + 1)
                    denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / max(1, self.avg_doc_length)))
                    score += idf * (num / max(0.001, denom))

            # 2. Exact Match identifier boost (e.g. error codes, exact symbol names)
            if query.lower() in doc.content.lower():
                score += 5.0

            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates: list[RetrievalCandidate] = []

        for idx, sc in scores[:top_k]:
            candidate = self.corpus[idx].model_copy()
            candidate.keyword_score = round(sc, 4)
            top_candidates.append(candidate)

        return top_candidates


bm25_retriever = BM25Retriever()
