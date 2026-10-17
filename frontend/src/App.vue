<template>
  <div class="app">
    <aside class="sidebar">
      <button class="new-chat" @click="startNewChat">＋ 新对话</button>
      <ul class="conv-list">
        <li
          v-for="c in conversations"
          :key="c.id"
          :class="{ active: c.id === conversationId }"
          @click="openConversation(c.id)"
        >
          {{ c.title }}
        </li>
      </ul>
    </aside>

    <main class="chat">
      <div class="messages" ref="scrollBox">
        <div v-if="messages.length === 0" class="empty">
          请输入你的 Python 文档问题开始对话
        </div>
        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div class="bubble" v-html="renderMarkdown(m.content)"></div>
          <div v-if="m.sources && m.sources.length" class="sources">
            <div class="src-title">参考来源：</div>
            <a
              v-for="(s, j) in m.sources"
              :key="j"
              :href="s.url"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ j + 1 }}. {{ s.title }}
            </a>
          </div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="bubble typing">正在思考…</div>
        </div>
      </div>

      <form class="input-bar" @submit.prevent="submit">
        <input
          v-model="draft"
          placeholder="请输入你的问题，回车发送"
          :disabled="loading"
        />
        <button type="submit" :disabled="loading || !draft.trim()">发送</button>
      </form>
    </main>
  </div>
</template>

<script>
import { marked } from 'marked'
import { getConversation, listConversations, sendQuestion } from './api'

export default {
  name: 'App',
  data() {
    return {
      conversations: [],
      conversationId: null,
      messages: [],
      draft: '',
      loading: false,
    }
  },
  async created() {
    await this.loadConversations()
  },
  methods: {
    renderMarkdown(text) {
      return marked.parse(text || '')
    },
    async loadConversations() {
      try {
        this.conversations = await listConversations()
      } catch (e) {
        console.error('加载会话失败', e)
      }
    },
    async openConversation(id) {
      this.conversationId = id
      try {
        const data = await getConversation(id)
        this.messages = data.messages || []
      } catch (e) {
        console.error('加载会话详情失败', e)
      }
      this.scrollToBottom()
    },
    startNewChat() {
      this.conversationId = null
      this.messages = []
    },
    async submit() {
      const question = this.draft.trim()
      if (!question || this.loading) return
      this.draft = ''
      this.messages.push({ role: 'user', content: question, sources: [] })
      this.loading = true
      this.scrollToBottom()
      try {
        const res = await sendQuestion(question, this.conversationId)
        this.conversationId = res.conversation_id
        this.messages.push({
          role: 'assistant',
          content: res.answer,
          sources: res.sources || [],
        })
        await this.loadConversations()
      } catch (e) {
        const msg = e.response && e.response.data && e.response.data.error
          ? e.response.data.error
          : e.message
        this.messages.push({
          role: 'assistant',
          content: '请求失败：' + msg,
          sources: [],
        })
      } finally {
        this.loading = false
        this.scrollToBottom()
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.scrollBox
        if (el) el.scrollTop = el.scrollHeight
      })
    },
  },
}
</script>
<style>
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  color: #1f2937;
}
.app {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 250px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  padding: 14px;
  overflow-y: auto;
  flex-shrink: 0;
}
.new-chat {
  width: 100%;
  padding: 10px;
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 12px;
  font-size: 14px;
}
.new-chat:hover {
  background: #f1f5f9;
}
.conv-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.conv-list li {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}
.conv-list li:hover {
  background: #eef2f7;
}
.conv-list li.active {
  background: #dbeafe;
}
.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.empty {
  color: #94a3b8;
  text-align: center;
  margin-top: 120px;
  font-size: 15px;
}
.msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}
.msg.user {
  align-items: flex-end;
}
.msg.assistant {
  align-items: flex-start;
}
.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 14px;
  line-height: 1.65;
  word-break: break-word;
}
.msg.user .bubble {
  background: #2563eb;
  color: #fff;
}
.msg.assistant .bubble {
  background: #f1f5f9;
  color: #111827;
}
.bubble p {
  margin: 0 0 8px;
}
.bubble p:last-child {
  margin-bottom: 0;
}
.bubble pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}
.bubble code {
  font-family: "Consolas", "Courier New", monospace;
  font-size: 13px;
}
.bubble pre code {
  background: transparent;
  padding: 0;
}
.typing {
  color: #64748b;
}
.sources {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 72%;
}
.src-title {
  font-weight: 600;
}
.sources a {
  color: #2563eb;
  text-decoration: none;
}
.sources a:hover {
  text-decoration: underline;
}
.input-bar {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid #e2e8f0;
}
.input-bar input {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-size: 15px;
}
.input-bar input:focus {
  outline: none;
  border-color: #2563eb;
}
.input-bar button {
  padding: 0 22px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
}
.input-bar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
