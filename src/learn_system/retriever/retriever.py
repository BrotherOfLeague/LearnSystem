"""检索器"""

import logging

from learn_system.embedding.base import EmbeddingProvider
from learn_system.models.chunk import Chunk
from learn_system.retriever.vector_store import SearchResult, VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """检索器"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        top_k: int = 8,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.top_k = top_k

    def retrieve(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        """检索相关文档块"""
        k = top_k or self.top_k

        # 生成查询的 embedding
        query_embedding = self.embedding_provider.embed(query)

        # 搜索最相似的块
        results = self.vector_store.search(query_embedding, k)

        logger.info(f"Retrieved {len(results)} chunks for query: {query[:50]}...")
        return results

    def retrieve_batch(self, queries: list[str]) -> list[list[SearchResult]]:
        """批量检索"""
        embeddings = self.embedding_provider.embed_batch(queries)
        all_results = []

        for query_embedding in embeddings:
            results = self.vector_store.search(query_embedding, self.top_k)
            all_results.append(results)

        return all_results

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """添加文档块到检索索引"""
        texts = [c.to_embedding_text() for c in chunks]
        embeddings = self.embedding_provider.embed_batch(texts)
        return self.vector_store.add_chunks(chunks, embeddings)

    def count(self) -> int:
        """返回索引中的块数量"""
        return self.vector_store.count()
