# Stage-Plan-04：Embedding 与 Chroma 索引

## 1. 目标
Embedding 与 Chroma 索引，为后续阶段提供可验证的基础能力。

## 2. 前置条件
Stage-Plan-03 已通过验收；总体需求和设计文档已阅读。

## 3. 任务清单
1. [x] 定义 EmbeddingProvider 与 VectorStore 接口。
2. [x] 在小样本上测试多语言 Embedding。
3. [x] 实现批量向量生成与错误处理。
4. [x] 写入 Chroma 并验证持久化。

## 4. 涉及文件
- `src/learn_system/embedding/base.py` - Embedding 接口定义
- `src/learn_system/embedding/local.py` - 本地 Embedding 实现（sentence-transformers）
- `src/learn_system/retriever/vector_store.py` - VectorStore 接口定义
- `src/learn_system/retriever/chroma_store.py` - Chroma 实现
- `tests/unit/test_embedding.py` - Embedding 测试
- `tests/unit/test_vector_store.py` - VectorStore 测试

## 5. 测试与验收
- [x] 向量可检索。
- [x] 结果包含原文和来源。
- [x] 模型与维度信息可追溯。

## 6. 执行记录
- 状态：✅ 已完成
- 开始日期：2026-01-10
- 完成日期：2026-01-10
- 备注：
  - Embedding 模型：BAAI/bge-m3（多语言支持）
  - 向量存储：Chroma（持久化）
  - 测试结果：42 passed

## 7. 交接到下一阶段
### 可运行命令
```bash
# 批量生成 embedding 并存入 Chroma
poetry run python -c "from learn_system.embedding.local import LocalEmbeddingProvider; ..."
```

### 测试结果
- pytest: 42 passed（总计）
- ruff check: All checks passed!
- ruff format: 6 files reformatted

### 已知问题
- 暂未实现完整的检索流程（Stage-05 处理）

### 下一阶段所需输入
- `data/processed/documents.jsonl` - 导入的文档数据
- Chroma 向量存储配置
