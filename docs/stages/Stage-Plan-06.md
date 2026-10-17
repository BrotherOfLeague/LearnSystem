# Stage-Plan-06：评估集与检索质量基线

## 1. 目标
建立固定评估集，量化检索质量，为后续混合检索与查询改写提供可比较的基线。

## 2. 前置条件
Stage-Plan-05 已通过验收；总体需求和设计文档已阅读。

## 3. 任务清单
1. [x] 建立 30 个中文问题与预期证据。
2. [x] 覆盖概念、精确 API、标准库、代码示例与边界问题。
3. [x] 实现 Recall@5 与 MRR 统计。
4. [x] 记录基线和典型失败案例。

## 4. 涉及文件
- `src/learn_system/evaluation/dataset.py` - 评估集（30 题）
- `src/learn_system/evaluation/metrics.py` - Recall@5 / MRR / Hit Rate
- `src/learn_system/cli/evaluate.py` - 评估命令
- `tests/unit/test_evaluation.py` - 指标单元测试

## 5. 测试与验收
- [x] 评估可重复执行。
- [x] 输出指标和错误案例。

## 6. 执行记录
- 状态：✅ 已完成
- 开始日期：2026-10-18
- 完成日期：2026-10-18
- 索引：581 篇文档，18,943 个分块（Chroma，cosine，bge-m3 fp16 GPU）
- 基线（top_k=5）：
  - Recall@5：0.7667
  - MRR：0.5506
  - Hit Rate：0.7667（23/30）
  - 按类别：stdlib 0.90 / example 0.75 / api 0.71 / boundary 0.67 / advanced 1.00 / concept 0.33
- 修复记录：
  - 指标按「页面」匹配，忽略 URL #anchor 片段
  - 评估集 URL 对齐 Python 3.15（library/ → builtins/ 的内置函数/类型页）

## 7. 交接到下一阶段
### 可运行命令
```bash
poetry run python -m learn_system.cli.evaluate --top-k 5 --output data/processed/evaluation_baseline.md
```

### 已知问题（交由 Stage-07/08 优化）
- 精确 API 类问题（enumerate/sorted 等）常命中 howto/functional、doctest 等相邻页，而非 builtins/functions.html
- 概念类（装饰器/生成器）召回偏弱（concept 类 Recall@5 仅 0.33）
- 纯向量检索对「精确术语」不敏感，需 BM25 + RRF 混合检索补强

### 下一阶段所需输入
- 固定评估集与基线报告
- Chroma 向量索引（18,943 块）
