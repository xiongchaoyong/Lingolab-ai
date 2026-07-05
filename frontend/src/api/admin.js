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

export function refreshInviteCodeApi(classId) {
  return request.post(`/api/admin/classes/${classId}/refresh-code`)
}

export function updateClassApi(classId, data) {
  return request.put(`/api/admin/classes/${classId}`, data)
}

export function deleteClassApi(classId) {
  return request.delete(`/api/admin/classes/${classId}`)
}

export function removeClassStudentApi(classId, userId) {
  return request.delete(`/api/admin/classes/${classId}/students/${userId}`)
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

export function setUserRoleApi(userId, role) {
  return request.put(`/api/admin/users/${userId}/role`, { role })
}

export function getUserDetailApi(userId) {
  return request.get(`/api/admin/users/${userId}`)
}

// ===== 仪表盘 =====

export function getDashboardApi(params = {}) {
  return request.get('/api/admin/dashboard', { params })
}

/** 教师工作台 Dashboard */
export function getTeacherDashboardApi() {
  return request.get('/api/admin/teacher-dashboard')
}

// ===== 学生报告 =====

export function getAllStudentsApi() {
  return request.get('/api/admin/students')
}

export function getStudentDetailApi(studentId) {
  return request.get(`/api/admin/students/${studentId}`)
}

export function getStudentTrendApi(studentId) {
  return request.get(`/api/admin/students/${studentId}/trend`)
}

export function getStudentCheckinStatsApi(studentId) {
  return request.get(`/api/admin/students/${studentId}/checkin-stats`)
}

// ===== 内容管理 =====

export function getContentListApi(contentType, params = {}) {
  return request.get(`/api/admin/content/${contentType}`, { params })
}

export function createContentApi(data) {
  return request.post('/api/admin/content', data)
}

export function updateContentApi(contentType, itemId, data) {
  return request.put(`/api/admin/content/${contentType}/${itemId}`, { content_type: contentType, data })
}

export function deleteContentApi(contentType, itemId) {
  return request.delete(`/api/admin/content/${contentType}/${itemId}`)
}

// ===== 反馈管理 =====

export function getFeedbacksApi(params = {}) {
  return request.get('/api/admin/feedbacks', { params })
}

export function replyFeedbackApi(feedbackId, reply) {
  return request.post(`/api/admin/feedbacks/${feedbackId}/reply`, { reply })
}

export function resolveFeedbackApi(feedbackId) {
  return request.put(`/api/admin/feedbacks/${feedbackId}/resolve`)
}

/** 用户端提交反馈 */
export function submitFeedbackApi(content, feedbackType) {
  return request.post('/api/feedback', { content, feedback_type: feedbackType })
}

// ===== 知识库管理 =====

export function getKnowledgeDocsApi(params = {}) {
  return request.get('/api/admin/knowledge', { params })
}

export function createKnowledgeDocApi(data) {
  return request.post('/api/admin/knowledge', data)
}

export function updateKnowledgeDocApi(docId, data) {
  return request.put(`/api/admin/knowledge/${docId}`, data)
}

export function deleteKnowledgeDocApi(docId) {
  return request.delete(`/api/admin/knowledge/${docId}`)
}

export function reindexKnowledgeDocApi(docId) {
  return request.post(`/api/admin/knowledge/${docId}/reindex`)
}

export function rebuildKnowledgeIndexApi() {
  return request.post('/api/admin/knowledge/rebuild-index')
}

export function getSearchLogsApi(params = {}) {
  return request.get('/api/admin/knowledge/logs', { params })
}