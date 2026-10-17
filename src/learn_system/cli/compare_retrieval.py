"""对比纯向量检索与混合检索（BM25 + RRF）的评估效果"""

import argparse
import logging

from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.evaluation import (
    EvaluationMetrics,
    evaluate_retriever,
    get_dataset,
)
from learn_system.retriever.bm25 import BM25Index, load_chunks
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.hybrid_retriever import HybridRetriever
from learn_system.retriever.retriever import Retriever

logger = logging.getLogger(__name__)


def build_comparison_report(vector: EvaluationMetrics, hybrid: EvaluationMetrics) -> str:
    """生成对比报告"""
    lines = [
        "# 检索方式对比报告",
        "",
        "## 总体指标",
        "",
        "| 指标 | 纯向量 | 混合(BM25+RRF) | 变化 |",
        "|---|---|---|---|",
        f"| Recall@5 | {vector.recall_at_5:.4f} | {hybrid.recall_at_5:.4f} | {hybrid.recall_at_5 - vector.recall_at_5:+.4f} |",
        f"| MRR | {vector.mrr:.4f} | {hybrid.mrr:.4f} | {hybrid.mrr - vector.mrr:+.4f} |",
        f"| Hit Rate | {vector.hit_rate:.4f} | {hybrid.hit_rate:.4f} | {hybrid.hit_rate - vector.hit_rate:+.4f} |",
        f"| 命中数 | {vector.hit_questions}/{vector.total_questions} | {hybrid.hit_questions}/{hybrid.total_questions} | |",
        "",
        "## 按类别 Recall@5",
        "",
        "| 类别 | 纯向量 | 混合 | 变化 |",
        "|---|---|---|---|",
    ]
    categories = sorted(set(vector.category_metrics) | set(hybrid.category_metrics))
    for cat in categories:
        v = vector.category_metrics.get(cat, {}).get("recall@5", 0.0)
        h = hybrid.category_metrics.get(cat, {}).get("recall@5", 0.0)
        lines.append(f"| {cat} | {v:.4f} | {h:.4f} | {h - v:+.4f} |")

    # 找出混合检索新命中/新丢失的问题
    vector_hit = {r.question.question for r in vector.question_results if r.is_hit}
    hybrid_hit = {r.question.question for r in hybrid.question_results if r.is_hit}
    gained = sorted(hybrid_hit - vector_hit)
    lost = sorted(vector_hit - hybrid_hit)

    if gained:
        lines.extend(["", "## 混合检索新增命中", ""])
        lines.extend(f"- {q}" for q in gained)
    if lost:
        lines.extend(["", "## 混合检索丢失的命中", ""])
        lines.extend(f"- {q}" for q in lost)

    lines.extend(
        [
            "",
            "## 结论",
            "",
            (
                "混合检索相对纯向量"
                f" Recall@5 {hybrid.recall_at_5 - vector.recall_at_5:+.4f}、"
                f" MRR {hybrid.mrr - vector.mrr:+.4f}。"
            ),
        ]
    )
    return "\n".join(lines)


def run_comparison(top_k: int = 5, output: str | None = None) -> int:
    """运行对比评估"""
    dataset = get_dataset()
    print(f"评估数据集: {len(dataset)} 个问题")

    print("\n初始化向量检索组件...")
    provider = LocalEmbeddingProvider(model_name=settings.embedding_model)
    store = ChromaVectorStore(persist_dir=settings.chroma_dir)
    vector_retriever = Retriever(
        vector_store=store, embedding_provider=provider, top_k=top_k
    )

    print("构建 BM25 关键词索引...")
    chunks = load_chunks(settings.processed_dir / "chunks.jsonl")
    bm25 = BM25Index(chunks)
    hybrid = HybridRetriever(
        vector_retriever=vector_retriever, bm25_index=bm25, vector_k=20, bm25_k=20
    )

    print(f"\n运行纯向量检索评估 (top_k={top_k})...")
    vector_metrics = evaluate_retriever(vector_retriever, dataset, top_k=top_k)

    print(f"\n运行混合检索评估 (top_k={top_k})...")
    hybrid_metrics = evaluate_retriever(hybrid, dataset, top_k=top_k)

    report = build_comparison_report(vector_metrics, hybrid_metrics)
    print("\n" + report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {output}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="对比纯向量与混合检索")
    parser.add_argument("--top-k", type=int, default=5, help="评估使用的 top_k (默认: 5)")
    parser.add_argument("--output", type=str, default=None, help="报告输出文件")
    args = parser.parse_args()
    raise SystemExit(run_comparison(args.top_k, args.output))


if __name__ == "__main__":
    main()
