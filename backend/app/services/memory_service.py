from __future__ import annotations
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict

from app.config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.warning("Qdrant client not installed. RAG features disabled.")


class MemoryService:
    def __init__(self):
        self._client: Optional[Any] = None
        self._collections: set[str] = set()
        self._bm25_indexes: dict[str, Any] = {}
        self._file_hashes: dict[str, dict[str, str]] = defaultdict(dict)

    async def initialize(self):
        if not HAS_QDRANT:
            logger.error("Qdrant not available. Install with: pip install qdrant-client")
            return

        try:
            self._client = QdrantClient(path=settings.qdrant_path)
            collections = self._client.get_collections()
            self._collections = {c.name for c in collections.collections}
            logger.info(
                "Qdrant initialized at %s with %d collections",
                settings.qdrant_path,
                len(self._collections),
            )
        except Exception as e:
            logger.error("Failed to initialize Qdrant: %s", e)
            self._client = None

    async def shutdown(self):
        if self._client:
            self._client.close()

    async def ensure_collection(self, project_id: str):
        if not self._client:
            return
        collection_name = f"project_{project_id}"
        if collection_name in self._collections:
            return

        try:
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=settings.embedding_dim,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="file_path",
                field_type=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="chunk_type",
                field_type=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            self._collections.add(collection_name)
            logger.info("Created collection %s", collection_name)
        except Exception as e:
            logger.error("Failed to create collection %s: %s", collection_name, e)

    async def index_chunks(
        self,
        project_id: str,
        chunks: list[dict[str, Any]],
    ):
        if not self._client:
            return
        await self.ensure_collection(project_id)
        collection_name = f"project_{project_id}"

        texts = [chunk["content"] for chunk in chunks]
        vectors = await embedding_service.embed(texts)

        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = hashlib.md5(
                f"{chunk['file_path']}:{chunk['line_start']}".encode()
            ).hexdigest()
            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "file_path": chunk["file_path"],
                        "language": chunk.get("language", ""),
                        "chunk_type": chunk.get("chunk_type", "code"),
                        "line_start": chunk.get("line_start", 0),
                        "line_end": chunk.get("line_end", 0),
                        "content": chunk["content"],
                        "git_hash": chunk.get("git_hash", ""),
                        "indexed_at": datetime.utcnow().isoformat(),
                    },
                )
            )

        if points:
            try:
                self._client.upsert(
                    collection_name=collection_name,
                    points=points,
                )
                logger.info(
                    "Indexed %d chunks for project %s",
                    len(points),
                    project_id,
                )
            except Exception as e:
                logger.error("Failed to index chunks: %s", e)

    async def search(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
        file_pattern: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if not self._client:
            return []

        collection_name = f"project_{project_id}"
        if collection_name not in self._collections:
            return []

        query_vector = await embedding_service.embed_single(query)

        filter_conditions = []
        if file_pattern:
            filter_conditions.append(
                qdrant_models.FieldCondition(
                    key="file_path",
                    match=qdrant_models.MatchText(text=file_pattern),
                )
            )

        try:
            results = self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit * 2,
                query_filter=qdrant_models.Filter(
                    must=filter_conditions if filter_conditions else None
                ),
            )

            search_results = []
            for res in results:
                search_results.append(
                    {
                        "file_path": res.payload.get("file_path", ""),
                        "content": res.payload.get("content", ""),
                        "score": res.score,
                        "chunk_type": res.payload.get("chunk_type", "code"),
                        "line_start": res.payload.get("line_start", 0),
                        "line_end": res.payload.get("line_end", 0),
                    }
                )

            return search_results[:limit]

        except Exception as e:
            logger.error("Search failed: %s", e)
            return []

    async def hybrid_search(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
        file_pattern: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        vector_results = await self.search(project_id, query, limit, file_pattern)

        keyword_results = await self._keyword_search(
            project_id, query, limit, file_pattern
        )

        return self._rrf_fuse(vector_results, keyword_results, limit)

    async def _keyword_search(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
        file_pattern: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            return []

        try:
            for col_name, bm25 in self._bm25_indexes.items():
                pass
        except Exception:
            pass
        return []

    def _rrf_fuse(
        self,
        vector_results: list[dict],
        keyword_results: list[dict],
        limit: int,
        k: int = 60,
    ) -> list[dict]:
        scores: dict[str, dict] = {}
        for rank, result in enumerate(vector_results):
            key = f"{result['file_path']}:{result['line_start']}"
            scores[key] = {**result, "_rrf_score": 1.0 / (k + rank + 1)}

        for rank, result in enumerate(keyword_results):
            key = f"{result['file_path']}:{result['line_start']}"
            if key in scores:
                scores[key]["_rrf_score"] += 1.0 / (k + rank + 1)
            else:
                scores[key] = {**result, "_rrf_score": 1.0 / (k + rank + 1)}

        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["_rrf_score"],
            reverse=True,
        )

        for r in sorted_results:
            r.pop("_rrf_score", None)

        return sorted_results[:limit]

    def update_file_hash(self, project_id: str, file_path: str, file_hash: str):
        self._file_hashes[project_id][file_path] = file_hash

    def get_file_hash(self, project_id: str, file_path: str) -> Optional[str]:
        return self._file_hashes[project_id].get(file_path)

    def needs_reindex(self, project_id: str, file_path: str, current_hash: str) -> bool:
        stored = self.get_file_hash(project_id, file_path)
        return stored != current_hash


memory_service = MemoryService()
