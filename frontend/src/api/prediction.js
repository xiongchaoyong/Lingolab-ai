import request from './index'

/** 获取当前学习预测 */
export function getPredictionApi() {
  return request.get('/api/prediction/current')
}

/** 设置目标分数 */
export function setTargetScoreApi(targetScore) {
  return request.put('/api/prediction/target', { target_score: targetScore })
}

/** 检查预警规则 */
export function checkAlertsApi() {
  return request.get('/api/prediction/alerts')
}

/** 获取通知列表 */
export function getNoticesApi(unreadOnly = false) {
  return request.get('/api/notices', { params: { unread_only: unreadOnly } })
}

/** 标记单条通知已读 */
export function markNoticeReadApi(id) {
  return request.put(`/api/notices/${id}/read`)
}

/** 标记全部通知已读 */
export function markAllNoticesReadApi() {
  return request.put('/api/notices/read-all')
}

/** 获取未读通知数量 */
export function getUnreadCountApi() {
  return request.get('/api/notices/unread-count')
}