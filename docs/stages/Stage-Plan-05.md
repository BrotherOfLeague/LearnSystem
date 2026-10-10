# Stage-Plan-05：基础 RAG 中文问答

## 1. 目标
基础 RAG 中文问答，为后续阶段提供可验证的基础能力。

## 2. 前置条件
Stage-Plan-04 已通过验收；总体需求和设计文档已阅读。

## 3. 任务清单
1. [x] 实现 Retriever 和 LLM Client。
2. [x] 构建证据约束的提示词。
3. [x] 根据真实元数据生成引用。
4. [x] 实现 CLI 连续问答和证据不足处理。

## 4. 涉及文件
- `src/learn_system/llm/base.py` - LLM 接口定义
- `src/learn_system/llm/openai_client.py` - OpenAI LLM 客户端
- `src/learn_system/retriever/retriever.py` - 检索器
- `src/learn_system/retriever/rag_engine.py` - RAG 引擎
- `src/learn_system/cli/main.py` - CLI 界面
- `tests/unit/test_llm.py` - LLM 测试
- `tests/unit/test_rag_engine.py` - RAG 引擎测试

## 5. 测试与验收
- [x] 中文问题得到中文回答。
- [x] 引用 URL 来自检索元数据。
- [x] 空结果时不编造答案。

## 6. 执行记录
- 状态：✅ 已完成
- 开始日期：2026-01-10
- 完成日期：2026-01-10
- 备注：
  - LLM 模型：gpt-4o-mini（默认）
  - 最小相关性阈值：0.3
  - 测试结果：50 passed

## 7. 交接到下一阶段
### 可运行命令
```bash
# 启动问答 CLI
poetry run python -m learn_system.cli.main
```

### 测试结果
- pytest: 50 passed（总计）
- ruff check: All checks passed!
- ruff format: 7 files reformatted

### 已知问题
- CLI 依赖 questionary 库

### 下一阶段所需输入
- 已索引的 Chroma 向量存储
- LLM API 配置
