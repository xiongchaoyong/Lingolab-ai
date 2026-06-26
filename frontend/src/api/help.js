import request from './index'

/**
 * 智能客服 — 文字聊天
 * @param {string} message - 用户消息
 * @param {Array} history - 对话历史 [{role:'user'|'ai', text:'...'}]
 * @returns {Promise<{reply: string, category: string, escalate: boolean}>}
 */
export function chatText(message, history = []) {
  return request.post('/api/help/chat', { message, history })
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