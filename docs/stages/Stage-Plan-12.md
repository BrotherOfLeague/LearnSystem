# Stage-Plan-12：后端对比与部署整理

## 1. 目标
整理部署与运维文档，评估是否需要迁移或增加检索后端，给出可复现的技术选型依据。

## 2. 前置条件
Stage-Plan-11 已通过验收。

## 3. 任务清单
1. [x] 保持统一 Retriever / VectorStore 接口。
2. [x] 评估 pgvector / Elasticsearch 引入必要性（结论：POC 不引入）。
3. [x] 补充 README 部署说明、配置说明、备份与恢复说明。
4. [x] 决定是否 Docker 化（结论：POC 阶段本地运行即可）。

## 4. 涉及文件
- `README.md` - 补充 Web 服务、环境变量、备份恢复章节
- `docs/stages/Stage-Plan-12.md` - 本文件

## 5. 决策记录

### 检索后端
- 保持 **Chroma**。理由：POC 阶段本地单机、19k 分块规模下 Chroma 完全够用；`VectorStore` 接口已抽象，后续若需要 SQL/全文检索/分布式再引入 pgvector 或 Elasticsearch，改动集中在适配器层。

### 部署方式
- POC 阶段以本地进程运行（Django `runserver` + Vite `dev`），**暂不 Docker 化**。理由：模型（2GB+）与索引等大数据均挂本地目录，Docker 化需处理卷挂载与 GPU 直通，复杂度大于收益；等需要多机/容器化部署时再补 Dockerfile。

### 备份恢复
- 关键数据均为本地文件（documents.jsonl / chunks.jsonl / storage/chroma / db.sqlite3），复制备份即可；原始文档与模型可重新下载。

## 6. 执行记录
- 状态：✅ 已完成
- 说明：README 已补齐部署、环境变量、备份恢复说明。

## 7. 后续建议（超出 POC 范围）
- 生产化：gunicorn/uvicorn 替代 runserver、Nginx 托管前端静态资源与反代。
- 后端扩展：若引入关系型查询或全文检索，实现 `PgVectorStore` / `ElasticsearchRetriever` 适配器并复用同一评估集。
- 容器化：Dockerfile + docker-compose（挂载 data/、storage/、models/ 卷）。
