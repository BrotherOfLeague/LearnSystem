"""Chroma 向量存储实现"""

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from learn_system.models.chunk import Chunk
from learn_system.retriever.vector_store import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """Chroma 向量存储"""

    COLLECTION_NAME = "learn_system_docs"

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str = COLLECTION_NAME,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client: chromadb.PersistentClient | None = None
        self._collection = None

    def _ensure_client(self) -> None:
        """确保客户端已初始化"""
        if self._client is None:
            if self.persist_dir:
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "LearnSystem document chunks"},
            )
            logger.info(f"Chroma collection '{self.collection_name}' ready")

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """添加分块到向量存储"""
        self._ensure_client()
        assert self._collection is not None

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.to_metadata() for c in chunks]

        self._collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )
        logger.info(f"Added {len(chunks)} chunks to Chroma")
        return len(chunks)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """搜索最相似的分块"""
        self._ensure_client()
        assert self._collection is not None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances", "metadatas"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                score = 1.0 - distance  # 转换为相似度

                chunk = Chunk(
                    chunk_id=metadata.get("chunk_id", chunk_id),
                    document_id=metadata.get("document_id", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    text=results["documents"][0][i] if results["documents"] else "",
                    section_path=metadata.get("section_path", []),
                    source_url=metadata.get("source_url"),
                    source_path=metadata.get("source_path", ""),
                    version=metadata.get("version", "3.12"),
                )
                search_results.append(SearchResult(chunk=chunk, score=score, distance=distance))

        return search_results

    def count(self) -> int:
        """返回分块数量"""
        self._ensure_client()
        assert self._collection is not None
        return self._collection.count()

    def clear(self) -> None:
        """清空向量存储"""
        self._ensure_client()
        assert self._client is not None
        self._client.delete_collection(self.collection_name)
        self._collection = None
        logger.info(f"Cleared collection '{self.collection_name}'")
