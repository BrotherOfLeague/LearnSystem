"""评估指标计算"""

import logging
from dataclasses import dataclass, field

from learn_system.evaluation.dataset import EvaluationQuestion
from learn_system.retriever.retriever import Retriever
from learn_system.retriever.vector_store import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class QuestionResult:
    """单个问题的评估结果"""

    question: EvaluationQuestion
    retrieved_results: list[SearchResult]
    hit_count: int = 0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    is_hit: bool = False
    error: str | None = None


@dataclass
class EvaluationMetrics:
    """评估指标"""

    recall_at_5: float = 0.0
    mrr: float = 0.0
    hit_rate: float = 0.0
    total_questions: int = 0
    hit_questions: int = 0
    category_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    difficulty_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    question_results: list[QuestionResult] = field(default_factory=list)


def _page_url(url: str | None) -> str:
    """去掉 URL 的 #anchor 片段，便于页面级匹配"""
    if not url:
        return ""
    return url.split("#", 1)[0]


def calculate_recall_at_k(
    retrieved_results: list[SearchResult],
    expected_urls: list[str],
    k: int = 5,
) -> float:
    """计算 Recall@K（按页面匹配，忽略锚点）"""
    if not expected_urls:
        return 0.0

    expected = {_page_url(u) for u in expected_urls}
    retrieved_urls = {
        _page_url(r.chunk.source_url) for r in retrieved_results[:k] if r.chunk.source_url
    }
    hits = sum(1 for u in expected if u in retrieved_urls)
    return hits / len(expected)


def calculate_mrr(
    retrieved_results: list[SearchResult],
    expected_urls: list[str],
) -> float:
    """计算 Mean Reciprocal Rank (MRR)"""
    if not expected_urls:
        return 0.0

    expected = {_page_url(u) for u in expected_urls}
    for i, result in enumerate(retrieved_results, 1):
        if _page_url(result.chunk.source_url) in expected:
            return 1.0 / i
    return 0.0


def check_hit(
    retrieved_results: list[SearchResult],
    expected_urls: list[str],
) -> bool:
    """检查是否有命中"""
    expected = {_page_url(u) for u in expected_urls}
    return any(
        _page_url(r.chunk.source_url) in expected for r in retrieved_results if r.chunk.source_url
    )


def evaluate_retriever(
    retriever: Retriever,
    questions: list[EvaluationQuestion],
    top_k: int = 5,
) -> EvaluationMetrics:
    """对检索器执行评估"""
    question_results: list[QuestionResult] = []
    category_stats: dict[str, dict[str, float]] = {}
    difficulty_stats: dict[str, dict[str, float]] = {}

    for q in questions:
        try:
            results = retriever.retrieve(q.question, top_k=top_k)
            recall = calculate_recall_at_k(results, q.expected_urls, k=5)
            mrr = calculate_mrr(results, q.expected_urls)
            is_hit = check_hit(results, q.expected_urls)
            expected_pages = {_page_url(u) for u in q.expected_urls}
            hit_count = sum(1 for r in results if _page_url(r.chunk.source_url) in expected_pages)

            q_result = QuestionResult(
                question=q,
                retrieved_results=results,
                hit_count=hit_count,
                recall_at_5=recall,
                mrr=mrr,
                is_hit=is_hit,
            )
            question_results.append(q_result)

            category_stats.setdefault(q.category, {"recall": 0.0, "mrr": 0.0, "count": 0})
            category_stats[q.category]["recall"] += recall
            category_stats[q.category]["mrr"] += mrr
            category_stats[q.category]["count"] += 1

            difficulty_stats.setdefault(q.difficulty, {"recall": 0.0, "mrr": 0.0, "count": 0})
            difficulty_stats[q.difficulty]["recall"] += recall
            difficulty_stats[q.difficulty]["mrr"] += mrr
            difficulty_stats[q.difficulty]["count"] += 1

        except Exception as e:
            logger.error(f"评估失败: {q.question}, 原因: {e}")
            question_results.append(QuestionResult(question=q, retrieved_results=[], error=str(e)))

    hit_count = sum(1 for r in question_results if r.is_hit)
    total = len(question_results)

    category_metrics: dict[str, dict[str, float]] = {}
    for cat, stats in category_stats.items():
        count = stats["count"]
        category_metrics[cat] = {
            "recall@5": stats["recall"] / count if count else 0.0,
            "mrr": stats["mrr"] / count if count else 0.0,
            "count": count,
        }

    difficulty_metrics: dict[str, dict[str, float]] = {}
    for diff, stats in difficulty_stats.items():
        count = stats["count"]
        difficulty_metrics[diff] = {
            "recall@5": stats["recall"] / count if count else 0.0,
            "mrr": stats["mrr"] / count if count else 0.0,
            "count": count,
        }

    return EvaluationMetrics(
        recall_at_5=sum(r.recall_at_5 for r in question_results) / total if total else 0.0,
        mrr=sum(r.mrr for r in question_results) / total if total else 0.0,
        hit_rate=hit_count / total if total else 0.0,
        total_questions=total,
        hit_questions=hit_count,
        category_metrics=category_metrics,
        difficulty_metrics=difficulty_metrics,
        question_results=question_results,
    )


def format_evaluation_report(metrics: EvaluationMetrics) -> str:
    """格式化评估报告"""
    lines = [
        "# 检索评估报告",
        "",
        "## 总体指标",
        f"- Recall@5: {metrics.recall_at_5:.4f}",
        f"- MRR: {metrics.mrr:.4f}",
        f"- Hit Rate: {metrics.hit_rate:.4f}",
        f"- 总问题数: {metrics.total_questions}",
        f"- 命中问题数: {metrics.hit_questions}",
        "",
        "## 按类别",
    ]

    for cat in sorted(metrics.category_metrics):
        m = metrics.category_metrics[cat]
        lines.append(
            f"- {cat}: Recall@5={m['recall@5']:.4f}, MRR={m['mrr']:.4f} (n={int(m['count'])})"
        )

    lines.extend(["", "## 按难度"])
    for diff in sorted(metrics.difficulty_metrics):
        m = metrics.difficulty_metrics[diff]
        lines.append(
            f"- {diff}: Recall@5={m['recall@5']:.4f}, MRR={m['mrr']:.4f} (n={int(m['count'])})"
        )

    failed = [r for r in metrics.question_results if not r.is_hit and not r.error]
    if failed:
        lines.extend(["", "## 失败案例 (前 5 个)"])
        for r in failed[:5]:
            lines.append(f"- Q: {r.question.question}")
            lines.append(f"  期望: {r.question.expected_urls[:2]}")
            if r.retrieved_results:
                lines.append(f"  实际: {r.retrieved_results[0].chunk.source_url}")
            lines.append("")

    return "\n".join(lines)
