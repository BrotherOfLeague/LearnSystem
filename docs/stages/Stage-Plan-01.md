# Stage-Plan-01：项目初始化与环境配置

## 1. 目标
项目初始化与环境配置，为后续阶段提供可验证的基础能力。

## 2. 前置条件
已安装 Python 3.12 与 Poetry；能在终端运行 `python --version` 和 `poetry --version`。

## 3. 任务清单
1. 建立 Poetry 项目并固定 Python 3.12。
2. 配置 pytest、基础目录、日志与配置加载。
3. 创建 .env.example 和 .gitignore。
4. 编写 README 中的环境安装与测试命令。

## 4. 涉及文件
- `pyproject.toml` - 项目配置
- `poetry.toml` - Poetry 配置
- `.env.example` - 环境变量示例
- `.gitignore` - Git 忽略文件
- `README.md` - 项目文档
- `src/learn_system/` - 源代码目录（config, models, loaders, parsers, chunker, embedding, retriever, llm, cli, api）
- `tests/` - 测试目录
- `.github/agents/stage-supervisor.agent.md` - Stage 监督 Agent
- `data/` - 数据目录（raw, processed）
- `storage/chroma/` - Chroma 向量存储目录

## 5. 测试与验收
- [x] 新环境可安装依赖。
- [x] 配置读取测试通过。
- [x] pytest 可运行。

## 6. 执行记录
- 状态：✅ 完成
- 开始日期：2026-10-10
- 完成日期：2026-10-10
- 备注：
  - 创建了完整的项目目录结构
  - 配置了 Poetry 项目和依赖
  - 实现了配置管理模块（settings.py, logging.py）
  - 创建了 .env.example 和 .gitignore
  - 编写了 README.md
  - 适配了 stage-supervisor.agent.md
  - 测试全部通过（5 个测试用例）
  - ruff 代码检查全部通过

## 7. 交接到下一阶段
完成本阶段所有验收项后，记录可运行命令、测试结果、已知问题和下一阶段所需输入，再开始下一个 Stage。

### 可运行命令
```bash
# 安装依赖
poetry install

# 运行测试
poetry run pytest -v

# 代码检查
poetry run ruff check .
poetry run ruff format --check .
```

### 测试结果
- pytest: 5 passed
- ruff check: All checks passed

### 下一阶段所需输入
- Python 官方 HTML 文档 ZIP 包（Python 3.12）
- 文档下载页面：https://docs.python.org/3.12/download.html
