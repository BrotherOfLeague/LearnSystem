# Stage-Plan-09：服务化（HTTP API）

## 1. 目标
把 RAG 能力暴露为 HTTP API，客户端可通过 HTTP 提问并获得回答与引用。

## 2. 前置条件
Stage-Plan-05 已通过验收。

## 3. 任务清单
1. [x] 将 RAG 能力与 CLI 解耦（服务层单例）。
2. [x] 增加健康检查与问答端点。
3. [x] 定义请求/响应模型。
4. [x] 处理参数校验与异常。
5. [x] 增加接口测试。

## 4. 技术选型说明（偏离原计划）
原计划使用 FastAPI，实际采用 **Django + DRF**（用户指定），接口能力等价：
- `POST /api/chat/` 问答（多轮）
- `GET/POST /api/conversations/` 会话
- `GET /api/health/` 健康检查

## 5. 涉及文件
- `backend/config/` - Django 配置与路由
- `backend/chat/` - models / serializers / views / urls / services / tests

## 6. 测试与验收
- [x] 客户端可通过 HTTP 发送问题并接收回答与引用。
- [x] 健康检查可用。
- [x] 接口测试通过（4 tests）。

## 7. 执行记录
- 状态：✅ 已完成（Django DRF 实现）
- 测试结果：backend 接口测试 4 passed，全套 pytest 79 passed
