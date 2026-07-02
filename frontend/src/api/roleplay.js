import request from './index'
import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function authHeaders(extra = {}) {
  const authStore = useAuthStore()
  const token = authStore.token
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra
}

/**
 * 流式开始角色扮演 — SSE 逐 token 返回
 * @param {string} role - interviewee/waiter/guide/doctor/teacher/customer_service/receptionist/colleague
 * @param {string} cefrLevel
 * @param {object} callbacks - { onToken(text), onDone(data), onError(err) }
 */
export async function streamStartRoleplay(role, cefrLevel, callbacks) {
  const resp = await fetch(`${API_BASE}/api/roleplay/stream/start`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ role, cefr_level: cefrLevel }),
  })
  await readSSEStream(resp, callbacks)
}

/**
 * 流式角色扮演对话 — 上传音频后 SSE 逐 token 返回 AI 回复
 * @param {string} sessionId
 * @param {string} role
 * @param {Blob} audioBlob
 * @param {object} callbacks - { onToken(text), onAsr(text), onGrammar(data), onDone(data), onError(err) }
 * @param {AbortSignal} signal - 用于取消上一次请求
 */
export async function streamSpeakRoleplay(sessionId, role, audioBlob, callbacks, signal) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('role', role)
  form.append('audio', audioBlob, 'recording.wav')
  const resp = await fetch(`${API_BASE}/api/roleplay/stream/speak`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
    signal,
  })
  await readSSEStream(resp, callbacks, signal)
}

async function readSSEStream(resp, callbacks, signal) {
  if (!resp.ok) {
    callbacks.onError?.(`HTTP ${resp.status}`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      // 检查是否已被取消
      if (signal?.aborted) {
        reader.cancel()
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            switch (data.type) {
              case 'token':
                callbacks.onToken?.(data.content)
                break
              case 'asr':
                callbacks.onAsr?.(data.text)
                break
              case 'done':
                callbacks.onDone?.(data)
                break
              case 'error':
                callbacks.onError?.(data.message)
                break
              case 'grammar':
                callbacks.onGrammar?.(data.data)
                break
              case 'translation':
                callbacks.onTranslation?.(data.data)
                break
            }
          } catch (e) {
            // skip malformed JSON
          }
        }
      }
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      // 请求被取消，静默处理
      return
    }
    callbacks.onError?.(e.message)
  }
}

/**
 * 开始角色扮演
 * @param {string} role
 * @param {string} cefrLevel
 * @returns {Promise<{session_id: string, ai_text: string, ai_audio_base64: string}>}
 */
export function startRoleplay(role = 'interviewee', cefrLevel = 'B1') {
  return request.post('/api/roleplay/start', {
    role,
    cefr_level: cefrLevel,
  })
}

/**
 * 用户说话 — 上传音频并获取 AI 角色回复
 * @param {string} sessionId
 * @param {string} role
 * @param {Blob} audioBlob
 * @returns {Promise<{user_text: string, ai_text: string, ai_audio_base64: string, conversation_complete: boolean}>}
 */
export function speakRoleplay(sessionId, role, audioBlob) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('role', role)
  form.append('audio', audioBlob, 'recording.wav')
  return request.post('/api/roleplay/speak', form, {
    timeout: 30000,
  })
}

/**
 * 结束角色扮演并获取评分
 * @param {string} sessionId
 * @returns {Promise<{overall: number, dimensions: Array, suggestions: string}>}
 */
export function endRoleplay(sessionId) {
  const form = new FormData()
  form.append('session_id', sessionId)
  return request.post('/api/roleplay/end', form, {
    timeout: 120000,
  })
}

/**
 * 流式 TTS — 返回音频流 URL，浏览器可直接作为 <audio> src 播放
 * @param {string} text
 * @param {string} voice
 * @returns {string} 音频流 URL
 */
export function ttsStreamUrl(text, voice = 'en-US-JennyNeural') {
  const params = new URLSearchParams({ text, voice })
  return `${API_BASE}/api/roleplay/tts/stream?${params.toString()}`
}

/**
 * 获取预取的 TTS 缓存音频 URL
 * @param {string} path - 后端返回的相对路径，如 /api/roleplay/tts/cached/xxx/0
 * @returns {string} 完整 URL
 */
export function ttsCachedUrl(path) {
  return `${API_BASE}${path}`
}

/**
 * 文本转语音（异步调用）
 * @param {string} text
 * @param {string} voice
 * @returns {Promise<{audio_base64: string}>}
 */
export function ttsRoleplay(text, voice = 'en-US-JennyNeural') {
  const form = new FormData()
  form.append('text', text)
  form.append('voice', voice)
  return request.post('/api/roleplay/tts', form, {
    timeout: 30000,
  })
}