# Stage-Plan-02：官方文档获取与解析

## 1. 目标
官方文档获取与解析，为后续阶段提供可验证的基础能力。

## 2. 前置条件
Stage-Plan-01 已通过验收；总体需求和设计文档已阅读。

## 3. 任务清单
1. [x] 导入 Python 3.12 官方 HTML 文档 ZIP。
2. [x] 实现文件遍历与 HTML 页面识别。
3. [x] 提取标题、正文、代码块、章节路径和来源 URL。
4. [x] 输出解析统计和失败文件清单。

## 4. 涉及文件
- `src/learn_system/models/document.py` - 文档数据模型
- `src/learn_system/loaders/document_loader.py` - 文档加载器
- `src/learn_system/loaders/import_docs.py` - 导入命令
- `src/learn_system/parsers/html_parser.py` - HTML 解析器
- `tests/unit/test_document.py` - 模型测试
- `tests/unit/test_document_loader.py` - 加载器测试
- `tests/unit/test_html_parser.py` - 解析器测试

## 5. 测试与验收
- [x] 代表性页面解析成功。
- [x] 代码和 URL 保留。
- [x] 解析失败可诊断。

## 6. 执行记录
- 状态：✅ 已完成
- 开始日期：2026-01-10
- 完成日期：2026-01-10
- 备注：
  - 新增依赖：beautifulsoup4, lxml
  - 测试结果：28 passed

## 7. 交接到下一阶段
### 可运行命令
```bash
# 导入文档（需要先解压 Python 官方 HTML 文档 ZIP）
poetry run python -m learn_system.loaders.import_docs --docs-dir ./data/raw --output-dir ./data/processed

# 统计导入结果
cat ./data/processed/import_stats.json
```

### 测试结果
- pytest: 28 passed
- ruff check: All checks passed!
- ruff format: 6 files reformatted

### 已知问题
- 当前未实现文档内容去重（后续 Chunking 阶段处理）
- 未实现增量导入（每次全量导入）

### 下一阶段所需输入
- `data/processed/documents.jsonl` - 导入的文档数据
- `data/processed/import_stats.json` - 导入统计信息
