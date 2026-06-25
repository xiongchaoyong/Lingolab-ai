import request from './index'

// ===== 班级管理 =====

export function getMyClassesApi() {
  return request.get('/api/admin/classes')
}

export function createClassApi(data) {
  return request.post('/api/admin/classes', data)
}

export function getClassStudentsApi(classId) {
  return request.get(`/api/admin/classes/${classId}/students`)
}

export function joinClassApi(inviteCode) {
  return request.post('/api/admin/classes/join', { invite_code: inviteCode })
}

// ===== 作业管理 =====

export function getAssignmentsApi() {
  return request.get('/api/admin/assignments')
}

export function createAssignmentApi(data) {
  return request.post('/api/admin/assignments', data)
}

export function getSubmissionsApi(assignmentId) {
  return request.get(`/api/admin/assignments/${assignmentId}/submissions`)
}

export function reviewSubmissionApi(submissionId, data) {
  return request.post(`/api/admin/submissions/${submissionId}/review`, data)
}

// ===== 用户管理 =====

export function getUsersApi(params = {}) {
  return request.get('/api/admin/users', { params })
}

export function setUserStatusApi(userId, isActive) {
  return request.put(`/api/admin/users/${userId}/status`, { is_active: isActive })
}

// ===== 仪表盘 =====

export function getDashboardApi() {
  return request.get('/api/admin/dashboard')
}