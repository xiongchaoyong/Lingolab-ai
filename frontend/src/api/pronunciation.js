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

/**
 * 获取跟读内容库
 * @param {string} contentType — 'word' 或 'sentence'
 * @param {string} cefrLevel — CEFR 难度：A1/A2/B1/B2
 * @param {string} keyword — 关键词搜索（模糊匹配 content_text + title）
 * @returns {Promise<Array>} 内容列表
 */
export function getContentList(contentType = null, cefrLevel = null, keyword = '') {
  const params = {}
  if (contentType) params.content_type = contentType
  if (cefrLevel) params.cefr_level = cefrLevel
  if (keyword) params.keyword = keyword
  return request.get('/api/pronunciation/content', { params })
}

/**
 * 获取评测历史记录
 * @param {number} limit — 返回条数
 * @returns {Promise<Array>} 评测记录列表
 */
export function getRecordList(limit = 20) {
  return request.get('/api/pronunciation/records', { params: { limit } })
}

/**
 * 验证英文文本合法性
 * @param {string} text — 待验证文本
 * @param {string} mode — 'word' 或 'sentence'
 * @returns {Promise<{valid: boolean, suggestion: string}>}
 */
export function validateTextApi(text, mode = 'word') {
  return request.post('/api/pronunciation/validate', { text, mode })
}
