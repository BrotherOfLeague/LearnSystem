"""混合检索：BM25 关键词检索 + 向量检索，RRF 融合"""

from learn_system.retriever.bm25 import BM25Index
from learn_system.retriever.retriever import Retriever
from learn_system.retriever.vector_store import SearchResult


def rrf_fusion(
    *result_lists: list[SearchResult],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[SearchResult]:
    """RRF（Reciprocal Rank Fusion）融合多个检索结果列表

    对每个列表中的第 rank 名，累加 weight/(k + rank)，再按总分降序排序并去重。
    最终 score 为归一化到 [0,1] 的 RRF 分数。
    """
    if weights is None:
        weights = [1.0] * len(result_lists)

    combined: dict[str, tuple[SearchResult, float]] = {}
    for results, weight in zip(result_lists, weights, strict=False):
        for rank, result in enumerate(results, 1):
            key = result.chunk.chunk_id
            if key not in combined:
                combined[key] = (result, 0.0)
            result, prev_score = combined[key]
            combined[key] = (result, prev_score + weight / (k + rank))

    ranked = sorted(combined.values(), key=lambda x: x[1], reverse=True)
    if not ranked:
        return []

    max_score = ranked[0][1]
    return [
        SearchResult(chunk=result.chunk, score=rrf / max_score if max_score else 0.0)
        for result, rrf in ranked
    ]


class HybridRetriever:
    """混合检索器：向量检索 + BM25，通过 RRF 融合排序"""

    def __init__(
        self,
        vector_retriever: Retriever,
        bm25_index: BM25Index,
        rrf_k: int = 60,
        vector_k: int = 20,
        bm25_k: int = 20,
        bm25_weight: float = 1.0,
    ):
        self.vector_retriever = vector_retriever
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.vector_k = vector_k
        self.bm25_k = bm25_k
        self.bm25_weight = bm25_weight

    def retrieve(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        """混合检索"""
        k = top_k or 8
        vector_results = self.vector_retriever.retrieve(query, self.vector_k)
        bm25_results = self.bm25_index.search(query, self.bm25_k)
        fused = rrf_fusion(
            vector_results, bm25_results, k=self.rrf_k, weights=[1.0, self.bm25_weight]
        )
        return fused[:k]

    def count(self) -> int:
        return self.vector_retriever.count()
