import request from './index'

/** 获取雷达图五维数据 */
export function getRadarDataApi(range = 'week') {
  return request.get('/api/progress/radar', { params: { range } })
}

/** 获取趋势折线图数据 */
export function getTrendDataApi(range = 'week') {
  return request.get('/api/progress/trend', { params: { range } })
}

/** 获取日历热力图数据 */
export function getHeatmapDataApi(year) {
  return request.get('/api/progress/heatmap', { params: { year } })
}

/** 获取6项核心统计 */
export function getStatsApi() {
  return request.get('/api/progress/stats')
}