import request from './index'

export function startAssessmentApi() {
  return request.post('/api/assessment/start')
}

export function submitAssessmentApi(sessionId, answers) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('answers', JSON.stringify(answers))
  return request.post('/api/assessment/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}