import request from './index'

/**
 * 智能客服 — 文字聊天（非流式）
 */
export function chatText(message, history = []) {
  return request.post('/api/help/chat', { message, history })
}

/**
 * 智能客服 — 文字聊天（流式 SSE）
 * @param {string} message - 用户消息
 * @param {Array} history - 对话历史
 * @returns {Promise<Response>} fetch Response 对象，用于读取 SSE 流
 */
export function chatStream(message, history = []) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  const token = localStorage.getItem('token') || ''
  return fetch(`${baseURL}/api/help/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, history }),
  })
}

/**
 * 智能客服 — 语音聊天
 * @param {Blob} audioBlob - 录音文件
 * @param {Array} history - 对话历史
 * @returns {Promise<{reply: string, category: string, escalate: boolean}>}
 */
export function chatVoice(audioBlob, history = []) {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  form.append('history', JSON.stringify(history))
  return request.post('/api/help/chat/voice', form, { timeout: 30000 })
}