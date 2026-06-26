import request from './index'

export function getMyClassesApi() {
  return request.get('/api/student/classes')
}

export function getMyAssignmentsApi() {
  return request.get('/api/student/assignments')
}

export function submitAssignmentApi(assignmentId, audioUrl) {
  return request.post(`/api/student/assignments/${assignmentId}/submit`, { audio_url: audioUrl })
}