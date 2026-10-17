# Stage-Plan-08：查询改写与可选重排

## 1. 目标
分析 Stage-06/07 失败案例，尝试用查询改写改善召回；评估重排的必要性。

## 2. 前置条件
Stage-Plan-07 已验收；已有基线（Recall@5=0.7667）与失败案例。

## 3. 任务清单
1. [x] 分析失败案例（装饰器/生成器/异常处理/格式化字符串等，共性是中文问句无英文术语）。
2. [x] 实现 LLM 查询改写（提取英文技术关键词并追加到查询）。
3. [x] 对比改写前后的质量与延迟。
4. [x] 评估重排必要性（结论：跳过，见下）。

## 4. 涉及文件
- `src/learn_system/retriever/query_processor.py` - QueryProcessor + RewriteRetriever
- `src/learn_system/cli/compare_rewrite.py` - 改写对比命令
- `tests/unit/test_query_processor.py` - 单元测试

## 5. 测试与验收
- [x] 改写前后质量与延迟可量化对比。

## 6. 执行记录
- 状态：✅ 已完成（结论：查询改写不启用；重排跳过）
- 测试结果：79 passed，ruff 全绿

### 对比结果（top_k=5，30 题）

| 指标 | 基线(原查询) | 改写后 | 变化 |
|---|---|---|---|
| Recall@5 | 0.7667 | 0.7667 | +0.0000 |
| MRR | 0.5506 | 0.5678 | +0.0172 |
| Hit Rate | 0.7667 | 0.7667 | +0.0000 |

改写平均延迟：**1.85 秒/问题**。新增命中 1 个（*args/**kwargs），丢失 1 个（可变/不可变对象）。

## 7. 结论与决策

1. **查询改写不启用**：MRR 仅 +0.017、Recall 无提升，却带来每问 ~1.85s 的额外 LLM 延迟与 API 依赖，收益不划算。
2. **重排跳过**：重排模型（如 bge-reranker）需额外下载约 1GB+ 模型，在当前网络环境成本高；且改写实验结果暗示重排的边际收益同样有限。留待有更强需求时再评估。

代码保留但默认不启用。当前检索仍为纯 bge-m3 向量检索（基线 Recall@5=0.7667）。

## 8. 交接到下一阶段
### 可运行命令
```bash
poetry run python -m learn_system.cli.compare_rewrite --top-k 5 --output data/processed/rewrite_comparison.md
```
