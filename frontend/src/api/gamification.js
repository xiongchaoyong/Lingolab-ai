import request from './index'

// ============================================================
// 每日闯关
// ============================================================

/** 获取今日闯关内容 */
export function getDailyChallengeApi() {
  return request.get('/api/gamification/daily-challenge')
}

/** 提交单关录音评分 */
export function submitLevelApi(audio, level) {
  const form = new FormData()
  form.append('audio', audio, 'recording.webm')
  form.append('level', level)
  return request.post('/api/gamification/daily-challenge/submit', form, {
    timeout: 30000,
  })
}

/** 完成每日闯关 */
export function completeDailyApi(levelsPassed) {
  const form = new FormData()
  form.append('levels_passed', levelsPassed)
  return request.post('/api/gamification/daily-challenge/complete', form)
}

// ============================================================
// 配音挑战
// ============================================================

/** 获取配音内容列表 */
export function getDubbingContentApi(difficulty) {
  return request.get('/api/gamification/dubbing/content', {
    params: difficulty ? { difficulty } : {},
  })
}

/** 提交配音录音 */
export function submitDubbingApi(audio, contentId) {
  const form = new FormData()
  form.append('audio', audio, 'recording.webm')
  form.append('content_id', contentId)
  return request.post('/api/gamification/dubbing/submit', form, {
    timeout: 30000,
  })
}

/** 获取配音历史 */
export function getDubbingRecordsApi(limit = 20) {
  return request.get('/api/gamification/dubbing/records', { params: { limit } })
}

// ============================================================
// 积分 & 勋章
// ============================================================

/** 获取用户勋章 */
export function getBadgesApi() {
  return request.get('/api/gamification/badges')
}

/** 获取积分总览 */
export function getPointsApi() {
  return request.get('/api/gamification/points')
}

/** 获取排行榜 */
export function getLeaderboardApi(limit = 20) {
  return request.get('/api/gamification/leaderboard', { params: { limit } })
}