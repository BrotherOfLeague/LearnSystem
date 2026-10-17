# Django + DRF 后端

为 LearnSystem RAG 能力提供 HTTP API。

## 启动

在**仓库根目录**执行（确保能读到 `.env` 和 `storage/`、`src/`）：

```bash
cd E:\GitHub\LearnSystem
poetry run python backend/manage.py runserver 0.0.0.0:8000
```

首次启动前初始化数据库：

```bash
poetry run python backend/manage.py migrate
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/chat/` | 提问，返回回答与来源（带 `conversation_id` 可多轮） |
| GET | `/api/conversations/` | 会话列表 |
| GET | `/api/conversations/{id}/` | 会话详情（含消息） |
| POST | `/api/conversations/` | 新建会话 |

### 提问示例

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "如何读取 JSON 文件？"}'
```

多轮追问：把返回的 `conversation_id` 带上即可。

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "那 sorted 呢？", "conversation_id": "<上一步返回的 id>"}'
```

## 测试

```bash
poetry run python backend/manage.py test chat
```
