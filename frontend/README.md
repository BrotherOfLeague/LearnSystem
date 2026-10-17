# Vue3 前端

LearnSystem 问答对话框前端（Vue3 + Vite）。

## 启动

需要 Node.js 18+。

```bash
cd E:\GitHub\LearnSystem\frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

> 开发时 Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`，所以要先启动 Django 后端。

## 功能

- 对话式提问（多轮追问，自动携带会话历史）
- 左侧会话列表（新建 / 切换 / 回看历史）
- 回答 Markdown 渲染（代码块高亮、列表等）
- 引用来源展示（可点击跳转官方文档）

## 生产构建

```bash
npm run build
```

构建产物在 `dist/`，可交给 Django 静态托管或任意静态服务器。
