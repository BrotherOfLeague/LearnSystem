"""评估命令"""

import argparse
import logging

from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.evaluation import (
    evaluate_retriever,
    format_evaluation_report,
    get_dataset,
    get_dataset_stats,
)
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.retriever import Retriever

logger = logging.getLogger(__name__)


def run_evaluation(
    top_k: int = 5,
    category: str | None = None,
    output: str | None = None,
) -> int:
    """运行检索评估，返回退出码"""
    print("=" * 60)
    print("Python 文档 RAG 检索评估")
    print("=" * 60)

    dataset = get_dataset()
    if category:
        dataset = [q for q in dataset if q.category == category]

    stats = get_dataset_stats()
    print(f"\n评估数据集: {len(dataset)} 个问题")
    print(f"类别分布: {stats['categories']}")
    print(f"难度分布: {stats['difficulties']}")

    print("\n初始化检索组件...")
    try:
        embedding_provider = LocalEmbeddingProvider(model_name=settings.embedding_model)
        vector_store = ChromaVectorStore(persist_dir=settings.chroma_dir)
        retriever = Retriever(
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            top_k=top_k,
        )

        count = retriever.count()
        if count == 0:
            print("错误: 向量索引为空。请先运行构建索引命令。")
            return 1
        print(f"向量索引中的块数量: {count}")
    except Exception as e:
        print(f"初始化失败: {e}")
        return 1

    print(f"\n运行评估 (top_k={top_k})...")
    try:
        metrics = evaluate_retriever(retriever, dataset, top_k=top_k)
        report = format_evaluation_report(metrics)
        print("\n" + report)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n报告已保存到: {output}")
    except Exception as e:
        print(f"评估失败: {e}")
        logger.exception("评估失败")
        return 1

    print("\n" + "=" * 60)
    print("评估摘要")
    print("=" * 60)
    print(f"Recall@5: {metrics.recall_at_5:.4f}")
    print(f"MRR:      {metrics.mrr:.4f}")
    print(f"Hit Rate: {metrics.hit_rate:.4f}")
    print(f"命中数:   {metrics.hit_questions}/{metrics.total_questions}")
    print("=" * 60)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="运行检索评估")
    parser.add_argument("--top-k", type=int, default=5, help="评估使用的 top_k (默认: 5)")
    parser.add_argument("--category", type=str, default=None, help="只评估指定类别")
    parser.add_argument("--output", type=str, default=None, help="报告输出文件")
    args = parser.parse_args()

    raise SystemExit(run_evaluation(args.top_k, args.category, args.output))


if __name__ == "__main__":
    main()
