"""评估指标测试"""

from learn_system.evaluation.dataset import EvaluationQuestion, get_dataset, get_dataset_stats
from learn_system.evaluation.metrics import (
    calculate_mrr,
    calculate_recall_at_k,
    check_hit,
    evaluate_retriever,
    format_evaluation_report,
)
from learn_system.models.chunk import Chunk
from learn_system.retriever.vector_store import SearchResult


def _results(urls):
    return [
        SearchResult(
            chunk=Chunk(
                chunk_id=f"c{i}",
                document_id="d",
                chunk_index=i,
                text="t",
                source_url=url,
            ),
            score=0.9,
        )
        for i, url in enumerate(urls)
    ]


def test_recall_at_k():
    results = _results(["https://a", "https://b", "https://c"])
    assert calculate_recall_at_k(results, ["https://a", "https://x"], k=5) == 0.5
    assert calculate_recall_at_k(results, ["https://x"], k=5) == 0.0
    assert calculate_recall_at_k([], ["https://a"], k=5) == 0.0


def test_mrr():
    results = _results(["https://a", "https://b"])
    assert calculate_mrr(results, ["https://b"]) == 0.5
    assert calculate_mrr(results, ["https://a"]) == 1.0
    assert calculate_mrr(results, ["https://z"]) == 0.0


def test_check_hit():
    assert check_hit(_results(["https://a"]), ["https://a"]) is True
    assert check_hit(_results(["https://a"]), ["https://b"]) is False


def test_metrics_strip_anchor_fragment():
    """测试页面级匹配：忽略 #anchor 片段"""
    results = _results(["https://docs.python.org/3.15/builtins/functions.html"])
    assert (
        calculate_recall_at_k(
            results,
            ["https://docs.python.org/3.15/builtins/functions.html#enumerate"],
            k=5,
        )
        == 1.0
    )
    assert (
        calculate_mrr(results, ["https://docs.python.org/3.15/builtins/functions.html#enumerate"])
        == 1.0
    )
    assert (
        check_hit(results, ["https://docs.python.org/3.15/builtins/functions.html#enumerate"])
        is True
    )


def test_dataset_has_30_questions_with_315_urls():
    dataset = get_dataset()
    assert len(dataset) == 30
    assert all(
        u.startswith("https://docs.python.org/3.15/") for q in dataset for u in q.expected_urls
    )
    assert get_dataset_stats()["total"] == 30


def test_evaluate_retriever_and_report():
    class FakeRetriever:
        def retrieve(self, query, top_k=5):
            return _results(["https://docs.python.org/3.15/library/json.html"])

    q = EvaluationQuestion(
        question="q",
        expected_urls=["https://docs.python.org/3.15/library/json.html"],
        category="stdlib",
        difficulty="easy",
    )
    metrics = evaluate_retriever(FakeRetriever(), [q], top_k=5)

    assert metrics.total_questions == 1
    assert metrics.hit_questions == 1
    assert metrics.recall_at_5 == 1.0
    assert "Recall@5" in format_evaluation_report(metrics)
