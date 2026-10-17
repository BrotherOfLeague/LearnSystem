"""对比查询改写前后的检索效果"""

import argparse
import logging
import time

from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.evaluation import (
    EvaluationMetrics,
    evaluate_retriever,
    get_dataset,
)
from learn_system.llm.openai_client import OpenAIClient
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.query_processor import QueryProcessor, RewriteRetriever
from learn_system.retriever.retriever import Retriever

logger = logging.getLogger(__name__)


def build_report(
    baseline: EvaluationMetrics, rewritten: EvaluationMetrics, latency: float
) -> str:
    lines = [
        "# 查询改写对比报告",
        "",
        "## 总体指标",
        "",
        "| 指标 | 基线(原查询) | 改写后 | 变化 |",
        "|---|---|---|---|",
        f"| Recall@5 | {baseline.recall_at_5:.4f} | {rewritten.recall_at_5:.4f} | {rewritten.recall_at_5 - baseline.recall_at_5:+.4f} |",
        f"| MRR | {baseline.mrr:.4f} | {rewritten.mrr:.4f} | {rewritten.mrr - baseline.mrr:+.4f} |",
        f"| Hit Rate | {baseline.hit_rate:.4f} | {rewritten.hit_rate:.4f} | {rewritten.hit_rate - baseline.hit_rate:+.4f} |",
        f"| 命中数 | {baseline.hit_questions}/{baseline.total_questions} | {rewritten.hit_questions}/{rewritten.total_questions} | |",
        "",
        f"改写平均延迟：{latency:.2f} 秒/问题",
        "",
    ]

    baseline_hit = {r.question.question for r in baseline.question_results if r.is_hit}
    rewritten_hit = {r.question.question for r in rewritten.question_results if r.is_hit}
    gained = sorted(rewritten_hit - baseline_hit)
    lost = sorted(baseline_hit - rewritten_hit)

    if gained:
        lines.extend(["", "## 改写后新增命中", ""])
        lines.extend(f"- {q}" for q in gained)
    if lost:
        lines.extend(["", "## 改写后丢失的命中", ""])
        lines.extend(f"- {q}" for q in lost)

    return "\n".join(lines)


def run_comparison(top_k: int = 5, output: str | None = None) -> int:
    dataset = get_dataset()
    print(f"评估数据集: {len(dataset)} 个问题")

    print("\n初始化检索组件...")
    provider = LocalEmbeddingProvider(model_name=settings.embedding_model)
    store = ChromaVectorStore(persist_dir=settings.chroma_dir)
    vector_retriever = Retriever(
        vector_store=store, embedding_provider=provider, top_k=top_k
    )
    llm = OpenAIClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=0.0,
    )
    rewrite_retriever = RewriteRetriever(vector_retriever, QueryProcessor(llm))

    print(f"\n运行基线评估 (top_k={top_k})...")
    baseline = evaluate_retriever(vector_retriever, dataset, top_k=top_k)

    print(f"\n运行查询改写评估 (top_k={top_k})...")
    t0 = time.time()
    rewritten = evaluate_retriever(rewrite_retriever, dataset, top_k=top_k)
    latency = (time.time() - t0) / len(dataset)

    report = build_report(baseline, rewritten, latency)
    print("\n" + report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {output}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="对比查询改写前后的检索效果")
    parser.add_argument("--top-k", type=int, default=5, help="评估使用的 top_k (默认: 5)")
    parser.add_argument("--output", type=str, default=None, help="报告输出文件")
    args = parser.parse_args()
    raise SystemExit(run_comparison(args.top_k, args.output))


if __name__ == "__main__":
    main()
