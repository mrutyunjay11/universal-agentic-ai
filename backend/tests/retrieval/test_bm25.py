import pytest
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.candidate import RetrievalCandidate


class TestBM25Retriever:
    def test_bm25_exact_error_and_identifier_matching(self):
        bm25 = BM25Retriever()

        docs = [
            RetrievalCandidate(
                document_id="doc_err",
                chunk_id="c1",
                source_id="logs",
                content="Error raised during initialization: ERR_MODULE_NOT_FOUND in path /usr/local/lib",
            ),
            RetrievalCandidate(
                document_id="doc_normal",
                chunk_id="c2",
                source_id="docs",
                content="Standard configuration guide for database pooling and memory limits.",
            ),
        ]

        bm25.index_documents(docs)

        # Search for exact technical identifier
        results = bm25.search("ERR_MODULE_NOT_FOUND", top_k=1)
        assert len(results) == 1
        assert results[0].document_id == "doc_err"
        assert results[0].keyword_score > 5.0  # Exact match identifier boost applied
