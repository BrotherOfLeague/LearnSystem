# Stage-Plan-11：文档更新与索引管理

## 1. 目标
支持基于内容哈希的增量导入、变更检测、失效块删除与索引状态查看。

## 2. 前置条件
Stage-Plan-05 已通过验收；已有完整索引。

## 3. 任务清单
1. [x] 基于内容哈希检测变更（source_hash）。
2. [x] 支持重复导入、变更更新与失效块删除。
3. [x] 管理 Python 文档版本（version 元数据已贯穿）。
4. [x] 提供索引重建与状态查看命令。

## 4. 涉及文件
- `src/learn_system/models/document.py` - ParsedDocument 增加 source_hash
- `src/learn_system/loaders/import_docs.py` - 增量导入
- `src/learn_system/retriever/chroma_store.py` - delete_by_document_ids / list_document_ids
- `src/learn_system/retriever/vector_store.py` - 接口补充
- `src/learn_system/cli/build_index.py` - 增量清理 + --status
- `tests/unit/test_import_docs.py` / `test_chroma_store.py`

## 5. 测试与验收
- [x] 重复导入不会无控制地增加重复块。
- [x] 版本元数据清晰（version 字段贯穿导入/分块/索引）。

## 6. 执行记录
- 状态：✅ 已完成
- 测试结果：81 passed，ruff 全绿

### 验证结果
- 增量导入：第二次导入 581 个文档全部复用（skipped_count=581，success=0）。
- 索引状态命令输出分块数 18943、文档数 581、模型与 collection 信息。
- 失效块清理：build_index 非 rebuild 模式下删除已不在文档集中的陈旧分块。

## 7. 可运行命令
```bash
# 增量导入（内容未变则复用）
poetry run python -m learn_system.loaders.import_docs --docs-dir ./data/raw --output-dir ./data/processed

# 全量重新解析
poetry run python -m learn_system.loaders.import_docs --docs-dir ./data/raw --output-dir ./data/processed --full

# 索引状态
poetry run python -m learn_system.cli.build_index --status

# 重建索引（清空重建）
poetry run python -m learn_system.cli.build_index --rebuild
```
