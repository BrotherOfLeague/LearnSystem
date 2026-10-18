import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 180000,
})

export async function sendQuestion(question, conversationId = null) {
  const { data } = await client.post('/chat/', {
    question,
    conversation_id: conversationId,
  })
  return data
}

export async function listConversations() {
  const { data } = await client.get('/conversations/')
  return data
}

export async function getConversation(id) {
  const { data } = await client.get(`/conversations/${id}/`)
  return data
}

export async function sendQuestionStream(question, conversationId, { onDelta, onDone, onError }) {
  const resp = await fetch('/api/chat/stream/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id: conversationId }),
  })

  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}))
    throw new Error(data.error || '请求失败')
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const dataLine = raw.split('\n').find((l) => l.startsWith('data: '))
      if (!dataLine) continue
      const payload = JSON.parse(dataLine.slice(6))
      if (payload.type === 'delta') onDelta(payload.text)
      else if (payload.type === 'done') onDone(payload)
      else if (payload.type === 'error') onError(new Error(payload.error))
    }
  }
}
