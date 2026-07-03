import request from './index'
import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function authHeaders(extra = {}) {
  const authStore = useAuthStore()
  const token = authStore.token
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra
}

/** SSE 流式读取器（共享实现） */
export async function readSSEStream(resp, callbacks, signal) {
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
              case 'token': callbacks.onToken?.(data.content); break
              case 'asr': callbacks.onAsr?.(data.text); break
              case 'done': callbacks.onDone?.(data); break
              case 'error': callbacks.onError?.(data.message); break
              case 'grammar': callbacks.onGrammar?.(data.data); break
              case 'translation': callbacks.onTranslation?.(data.data); break
              case 'hint': callbacks.onHint?.(data.data); break
            }
          } catch (e) { /* skip malformed JSON */ }
        }
      }
    }
  } catch (e) {
    if (e.name === 'AbortError') return
    callbacks.onError?.(e.message)
  }
}

/** 流式开始对话 */
export async function streamStart(topic, cefrLevel, mode, callbacks) {
  const resp = await fetch(`${API_BASE}/api/voice-chat/stream/start`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ topic, cefr_level: cefrLevel, mode }),
  })
  await readSSEStream(resp, callbacks)
}

/** 流式说话 */
export async function streamSpeak(sessionId, topic, audioBlob, callbacks, signal) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('audio', audioBlob, 'recording.wav')
  const resp = await fetch(`${API_BASE}/api/voice-chat/stream/speak`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
    signal,
  })
  await readSSEStream(resp, callbacks, signal)
}

/** 开始对话（非流式） */
export function startChat(topic, cefrLevel = 'B1', mode = 'scene') {
  return request.post('/api/voice-chat/start', { topic, cefr_level: cefrLevel, mode })
}

/** 说话（非流式） */
export function speakChat(sessionId, topic, audioBlob) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('audio', audioBlob, 'recording.wav')
  return request.post('/api/voice-chat/speak', form, { timeout: 30000 })
}

/** 结束对话并评分 */
export function endChat(sessionId) {
  const form = new FormData()
  form.append('session_id', sessionId)
  return request.post('/api/voice-chat/end', form, { timeout: 120000 })
}

/** 流式 TTS URL */
export function ttsStreamUrl(text, voice = 'en-US-JennyNeural') {
  const params = new URLSearchParams({ text, voice })
  return `${API_BASE}/api/voice-chat/tts/stream?${params.toString()}`
}

/** TTS 缓存 URL */
export function ttsCachedUrl(path) {
  return `${API_BASE}${path}`
}

/** 异步 TTS */
export function ttsChat(text, voice = 'en-US-JennyNeural') {
  const form = new FormData()
  form.append('text', text)
  form.append('voice', voice)
  return request.post('/api/voice-chat/tts', form)
}

/** 获取对话历史 */
export function getSessions(limit = 10) {
  return request.get('/api/voice-chat/sessions', { params: { limit } })
}
