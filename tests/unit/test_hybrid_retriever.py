"""混合检索 RRF 融合测试"""

from learn_system.models.chunk import Chunk
from learn_system.retriever.hybrid_retriever import rrf_fusion
from learn_system.retriever.vector_store import SearchResult


def _result(cid: str, score: float) -> SearchResult:
    return SearchResult(
        chunk=Chunk(chunk_id=cid, document_id="d", chunk_index=0, text="t"),
        score=score,
    )


def test_rrf_fusion_dedupes_and_ranks():
    # c2 出现在两个列表里（应被去重并提升排名）
    vector = [_result("c1", 0.9), _result("c2", 0.8)]
    bm25 = [_result("c2", 1.0), _result("c3", 0.7)]

    fused = rrf_fusion(vector, bm25, k=60)

    ids = [r.chunk.chunk_id for r in fused]
    assert "c2" in ids
    assert len(ids) == 3  # 去重后 3 个唯一结果
    assert ids[0] == "c2"  # 出现在两个列表里，RRF 分最高


def test_rrf_fusion_single_list():
    results = [_result("c1", 0.9), _result("c2", 0.8)]
    fused = rrf_fusion(results, k=60)
    assert [r.chunk.chunk_id for r in fused] == ["c1", "c2"]


def test_rrf_fusion_empty():
    assert rrf_fusion([], []) == []
