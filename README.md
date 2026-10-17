# LearnSystem

Python Docs RAG：基于 Python 官方文档的中文智能问答知识库。

## 项目概述

将 Python 官方文档下载并建立本地可检索的知识库，允许用户使用中文提问，由大语言模型基于检索到的英文官方文档生成中文回答，并提供可核查的官方来源链接。

## 功能特性

- 支持中文问题检索英文 Python 官方文档
- 回答尽可能准确，并提供官方文档出处
- 保留函数名、参数名、异常名、代码和英文技术术语
- 采用可替换的检索后端（Chroma、pgvector、Elasticsearch）
- 分阶段开发，先完成最小可用版本，再优化检索质量

## 环境安装

### 前置要求

- Python 3.12+
- Poetry 2.0+

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/LearnSystem.git
cd LearnSystem

# 2. 安装依赖
poetry install

# 3. 复制并配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置

# 4. 运行测试
poetry run pytest

# 5. 代码检查
poetry run ruff check .
poetry run ruff format --check .
```

## 项目结构

```
LearnSystem/
├── src/learn_system/     # 源代码
│   ├── config/           # 配置管理
│   ├── models/           # 数据模型
│   ├── loaders/          # 文档加载器
│   ├── parsers/          # HTML 解析器
│   ├── chunker/          # 文本分块器
│   ├── embedding/        # Embedding 接口
│   ├── retriever/        # 检索器接口
│   ├── llm/              # LLM 客户端
│   ├── cli/              # 命令行界面
│   └── api/              # API 接口
├── tests/                # 测试代码
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/         # 测试固件
├── data/                 # 数据目录
│   ├── raw/              # 原始文档
│   └── processed/        # 处理后数据
├── storage/              # 存储目录
│   └── chroma/           # Chroma 向量存储
├── docs/                 # 文档
│   ├── 需求文档.md
│   ├── 设计文档.md
│   ├── 整体开发计划.md
│   └── stages/           # 各阶段计划
├── pyproject.toml        # 项目配置
└── .env.example          # 环境变量示例
```

## 开发阶段

| Stage | 名称 | 说明 |
|-------|------|------|
| Stage-01 | 项目初始化 | Poetry 项目、目录、配置与测试框架 |
| Stage-02 | 文档导入 | HTML 文档导入、解析器 |
| Stage-03 | 文本分块 | Chunker、分块产物 |
| Stage-04 | 向量索引 | Embedding 接口、Chroma 索引 |
| Stage-05 | 基础问答 | Retriever、LLM Client、CLI |
| Stage-06~12 | 后续优化 | 评估、混合检索、Web UI 等 |

## 使用方法

### 导入文档

```bash
poetry run python -m learn_system.loaders.import_docs --docs-dir ./data/raw --output-dir ./data/processed
```

### 构建索引

```bash
# 完整构建（生成 chunks.jsonl 并写入 Chroma 向量索引）
poetry run python -m learn_system.cli.build_index

# 只生成分块，不生成向量
poetry run python -m learn_system.cli.build_index --no-embed

# 重建索引
poetry run python -m learn_system.cli.build_index --rebuild
```

### 启动问答

```bash
poetry run python -m learn_system.cli.main
```

### 运行检索评估

```bash
poetry run python -m learn_system.cli.evaluate --top-k 5
```

### 运行测试

```bash
poetry run pytest -v
poetry run pytest --cov=learn_system
```

## 许可证

MIT License
