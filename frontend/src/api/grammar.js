import request from './index'

/**
 * 语法纠错 — 文本输入
 * @param {string} text - 待纠错的英文文本
 * @param {string} cefrLevel - CEFR 等级
 * @returns {Promise<{
 *   original_text: string,
 *   corrected_text: string,
 *   errors: Array<{original, correction, error_type, explanation}>,
 *   polished_version: string,
 *   suggestions: string[]
 * }>}
 */
export function correctGrammar(text, cefrLevel = 'B1') {
  const form = new FormData()
  form.append('text', text)
  form.append('cefr_level', cefrLevel)
  return request.post('/api/grammar/correct', form, { timeout: 30000 })
}

/**
 * 语法纠错 — 语音输入
 * @param {Blob} audioBlob - 用户录音
 * @param {string} cefrLevel - CEFR 等级
 * @returns {Promise<同上>}
 */
export function correctGrammarVoice(audioBlob, cefrLevel = 'B1') {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.wav')
  form.append('cefr_level', cefrLevel)
  return request.post('/api/grammar/correct/voice', form, { timeout: 45000 })
}