import request from './index'

/** 获取今日资料推荐 */
export function getRecommendationsApi() {
  return request.get('/api/recommendations/')
}

/** 不感兴趣 */
export function dislikeRecommendationApi(id) {
  return request.post(`/api/recommendations/${id}/dislike`)
}

/** 换一批推荐 */
export function refreshRecommendationsApi() {
  return request.post('/api/recommendations/refresh')
}

/** 记录点击/完成 */
export function clickRecommendationApi(id, action) {
  return request.post(`/api/recommendations/${id}/click`, { action })
}