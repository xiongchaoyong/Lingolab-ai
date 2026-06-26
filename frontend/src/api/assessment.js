import request from './index'

export function startAssessmentApi() {
  return request.post('/api/assessment/start')
}

export function answerQuestionApi(sessionId, questionId, answer, audioBlob = null, mimeType = null) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('question_id', questionId)
  formData.append('answer', answer || '')

  if (audioBlob) {
    const ext = (mimeType || '').includes('webm') ? 'webm' : 'wav'
    formData.append('audio', audioBlob, `speaking.${ext}`)
  }

  return request.post('/api/assessment/answer', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function completeAssessmentApi(sessionId) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  return request.post('/api/assessment/complete', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function restoreSessionApi(sessionId) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  return request.post('/api/assessment/restore', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}