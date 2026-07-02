import request from './index'
import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function authHeaders(extra = {}) {
  const authStore = useAuthStore()
  const token = authStore.token
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra
}

/**
 * 流式开始新对话 — SSE 逐 token 返回
 * @param {string} scene
 * @param {string} cefrLevel
 * @param {object} callbacks - { onToken(text), onAsr(text), onGrammar(data), onDone(data), onError(err) }
 */
export async function streamStartConversation(scene, cefrLevel, callbacks) {
  const resp = await fetch(`${API_BASE}/api/conversation/stream/start`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ scene, cefr_level: cefrLevel }),
  })
  await readSSEStream(resp, callbacks)
}

/**
 * 流式对话 — 上传音频后 SSE 逐 token 返回 AI 回复
 * @param {string} sessionId
 * @param {string} scene
 * @param {Blob} audioBlob
 * @param {object} callbacks - { onToken(text), onAsr(text), onGrammar(data), onDone(data), onError(err) }
 * @param {AbortSignal} signal - 用于取消上一次请求
 */
export async function streamSpeakConversation(sessionId, scene, audioBlob, callbacks, signal) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('scene', scene)
  form.append('audio', audioBlob, 'recording.wav')
  const resp = await fetch(`${API_BASE}/api/conversation/stream/speak`, {
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
              case 'hint':
                callbacks.onHint?.(data.data)
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
 * 开始新对话
 * @param {string} scene - 场景: self_intro/directions/shopping/restaurant/hotel/airport/hospital/school
 * @param {string} cefrLevel - CEFR 等级: A1/A2/B1/B2
 * @returns {Promise<{session_id: string, ai_text: string, ai_audio_base64: string}>}
 */
export function startConversation(scene = 'self_intro', cefrLevel = 'B1') {
  return request.post('/api/conversation/start', {
    scene,
    cefr_level: cefrLevel,
  })
}

/**
 * 用户说话 — 上传音频并获取 AI 回复
 * @param {string} sessionId - 会话 ID
 * @param {string} scene - 场景标识
 * @param {Blob} audioBlob - 用户录音 Blob
 * @returns {Promise<{user_text: string, ai_text: string, ai_audio_base64: string, grammar_correction: object|null, conversation_complete: boolean}>}
 */
export function speakConversation(sessionId, scene, audioBlob) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('scene', scene)
  form.append('audio', audioBlob, 'recording.wav')
  return request.post('/api/conversation/speak', form, {
    timeout: 30000,
  })
}

/**
 * 结束对话并获取评分
 * @param {string} sessionId - 会话 ID
 * @returns {Promise<{overall: number, dimensions: Array, suggestions: string}>}
 */
export function endConversation(sessionId) {
  console.log('[END] session_id:', sessionId)
  const form = new FormData()
  form.append('session_id', sessionId)
  return request.post('/api/conversation/end', form, {
    timeout: 120000,  // 评分耗时较长（wav2vec2 + LLM），2分钟超时
  }).catch(e => {
    console.error('[END] request failed:', e.response?.status, e.response?.data)
    throw e
  })
}

/**
 * 流式 TTS — 返回音频流 URL，浏览器可直接作为 <audio> src 播放
 * @param {string} text - 要合成的文本
 * @param {string} voice - 音色
 * @returns {string} 音频流 URL
 */
export function ttsStreamUrl(text, voice = 'en-US-JennyNeural') {
  const params = new URLSearchParams({ text, voice })
  return `${API_BASE}/api/conversation/tts/stream?${params.toString()}`
}

/**
 * 获取预取的 TTS 缓存音频 URL
 * @param {string} path - 后端返回的相对路径，如 /api/conversation/tts/cached/xxx/0
 * @returns {string} 完整 URL
 */
export function ttsCachedUrl(path) {
  return `${API_BASE}${path}`
}

/**
 * 文本转语音（异步调用，不阻塞对话流程）
 * @param {string} text - 要合成的文本
 * @param {string} voice - 音色
 * @returns {Promise<{audio_base64: string}>}
 */
export function ttsConversation(text, voice = 'en-US-JennyNeural') {
  const form = new FormData()
  form.append('text', text)
  form.append('voice', voice)
  return request.post('/api/conversation/tts', form)
}

/**
 * 获取对话历史
 * @param {number} limit - 返回条数
 * @returns {Promise<Array>} 对话会话列表
 */
export function getConversationSessions(limit = 10) {
  return request.get('/api/conversation/sessions', { params: { limit } })
}