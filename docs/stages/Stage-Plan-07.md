# Stage-Plan-07：BM25 + RRF 混合检索

## 1. 目标
实现 BM25 关键词检索 + RRF 融合，对比混合检索与纯向量检索的效果，决定是否启用。

## 2. 前置条件
Stage-Plan-06 已通过验收；已有固定评估集与基线（Recall@5=0.7667）。

## 3. 任务清单
1. [x] 建立 BM25 关键词索引。
2. [x] 实现 RRF 排名融合与去重。
3. [x] 实现混合检索器（向量 + BM25）。
4. [x] 对比纯向量与混合检索的评估结果。

## 4. 涉及文件
- `src/learn_system/retriever/bm25.py` - BM25 索引与分词
- `src/learn_system/retriever/hybrid_retriever.py` - RRF 融合 + 混合检索器
- `src/learn_system/cli/compare_retrieval.py` - 对比评估命令
- `tests/unit/test_bm25.py` / `tests/unit/test_hybrid_retriever.py` - 单元测试

## 5. 测试与验收
- [x] 函数名和术语查询可测。
- [x] 有可复现对比报告。

## 6. 执行记录
- 状态：✅ 已完成（结论：不启用混合检索）
- 开始日期：2026-10-18
- 完成日期：2026-10-18
- 测试结果：75 passed，ruff 全绿

### 对比结果（top_k=5，30 题）

| 指标 | 纯向量 | 混合(BM25+RRF) | 变化 |
|---|---|---|---|
| Recall@5 | 0.7667 | 0.7000 | **-0.0667** |
| MRR | 0.5506 | 0.4894 | -0.0611 |
| Hit Rate | 0.7667 | 0.7000 | -0.0667 |

混合检索仅新增命中 1 个（enumerate），但丢失 3 个（filter / map / isinstance）。

## 7. 结论与决策

**不启用混合检索，保持纯向量检索。**

原因分析：
- bge-m3 对中文问题 → 英文文档的跨语言语义检索已经较强，API 名（map/filter/sorted 等）在中文问句中也能被向量检索命中；
- BM25 对 map/filter/isinstance 这类高频函数名返回大量噪声（这些词在文档中广泛出现），RRF 融合时把向量检索的正确结果挤出了 top-5；
- 停用词过滤（含 "python" 等）小幅缓解但未能扭转；加权 RRF（降低 BM25 权重）效果更差。

代码保留但默认不启用：`HybridRetriever` 已实现，后续若引入更精细的分词 / 词权重 / 查询改写（Stage-08）可重新评估。

## 8. 交接到下一阶段
### 可运行命令
```bash
poetry run python -m learn_system.cli.compare_retrieval --top-k 5 --output data/processed/retrieval_comparison.md
```

### 下一阶段所需输入
- 对比报告与失败案例（filter/map/isinstance 等高频函数名）
- 纯向量检索基线（Recall@5=0.7667）
