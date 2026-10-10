# Stage-Plan-03：文本分块与元数据

## 1. 目标
文本分块与元数据，为后续阶段提供可验证的基础能力。

## 2. 前置条件
Stage-Plan-02 已通过验收；总体需求和设计文档已阅读。

## 3. 任务清单
1. [x] 定义 Document 与 Chunk 模型。
2. [x] 按章节、段落、列表和代码块切分。
3. [x] 生成稳定 ID 与内容哈希。
4. [x] 输出可检查的 JSONL 分块结果。

## 4. 涉及文件
- `src/learn_system/models/chunk.py` - 分块数据模型（Chunk, ChunkingResult）
- `src/learn_system/chunker/rule_based_chunker.py` - 基于规则的分块器
- `tests/unit/test_chunker.py` - 分块器测试

## 5. 测试与验收
- [x] Chunk 元数据齐全。
- [x] 代码块不会被随意截断。
- [x] 重复内容可检测。

## 6. 执行记录
- 状态：✅ 已完成
- 开始日期：2026-01-10
- 完成日期：2026-01-10
- 备注：
  - 分块策略：按段落边界 + 句子边界切分
  - 代码块保留完整性（≥MIN_CODE_LINES*20 字符）
  - token 估算：中文字符 / 1.5 + 其他字符 / 4
  - 测试结果：38 passed

## 7. 交接到下一阶段
### 可运行命令
```bash
# 分块文档（需要先完成 Stage-02 的文档导入）
poetry run python -c "from learn_system.loaders.import_docs import import_documents; ..."
```

### 测试结果
- pytest: 38 passed（总计）
- ruff check: All checks passed!
- ruff format: 3 files reformatted

### 已知问题
- 暂未实现与向量存储的集成（Stage-04 处理）

### 下一阶段所需输入
- `data/processed/documents.jsonl` - 导入的文档数据
