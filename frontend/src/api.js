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
