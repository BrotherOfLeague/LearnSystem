"""评估模块"""

from learn_system.evaluation.dataset import (
    EVALUATION_DATASET,
    EvaluationQuestion,
    get_dataset,
    get_dataset_by_category,
    get_dataset_stats,
)
from learn_system.evaluation.metrics import (
    EvaluationMetrics,
    QuestionResult,
    calculate_mrr,
    calculate_recall_at_k,
    check_hit,
    evaluate_retriever,
    format_evaluation_report,
)

__all__ = [
    # 数据集
    "EVALUATION_DATASET",
    "EvaluationQuestion",
    "get_dataset",
    "get_dataset_by_category",
    "get_dataset_stats",
    # 指标
    "EvaluationMetrics",
    "QuestionResult",
    "calculate_mrr",
    "calculate_recall_at_k",
    "check_hit",
    "evaluate_retriever",
    "format_evaluation_report",
]
