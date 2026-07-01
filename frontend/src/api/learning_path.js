import request from './index'

/** 获取今日任务列表（含进度） */
export function getDailyTasksApi() {
  return request.get('/api/learning-path/tasks')
}

/** 跳过任务 */
export function skipTaskApi(taskId, reason = null) {
  return request.post(`/api/learning-path/tasks/${taskId}/skip`, { reason })
}

/** 换一个同类型任务 */
export function replaceTaskApi(taskId) {
  return request.post(`/api/learning-path/tasks/${taskId}/replace`)
}

/** 调整任务难度 */
export function adjustDifficultyApi(taskId, direction) {
  return request.post(`/api/learning-path/tasks/${taskId}/adjust-difficulty`, { direction })
}

/** 获取历史记录 */
export function getHistoryApi(days = 7) {
  return request.get('/api/learning-path/history', { params: { days } })
}

/** 获取个人情况说明 */
export function getProfileSummaryApi() {
  return request.get('/api/learning-path/profile-summary')
}

/** 完成任务并记录分数 */
export function completeTaskApi(taskId, data) {
  return request.post(`/api/learning-path/tasks/${taskId}/complete`, data)
}