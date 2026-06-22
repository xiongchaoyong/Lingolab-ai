import request from './index'

/**
 * 发音评测 — 上传音频 + 标准文本 + 模式，获取五维评分
 * @param {Blob} audioBlob — 录音 Blob
 * @param {string} text — 跟读的标准文本
 * @param {string} mode — 跟读模式：word/sentence，影响综合分权重
 * @returns {Promise<{overall: number, dimensions: Array, errors: Array, char_scores: Array}>}
 */
export function scorePronunciation(audioBlob, text, mode = 'word') {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.wav')
  form.append('text', text)
  form.append('mode', mode)
  // 不手动设置 Content-Type，让 axios 自动添加 multipart/form-data + boundary
  return request.post('/api/pronunciation/score', form, {
    timeout: 30000,
  })
}
