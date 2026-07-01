import request from './index'

// ===== 语音挑战 =====

/** 获取挑战列表 */
export function getChallengesApi() {
  return request.get('/api/community/challenges')
}

/** 提交挑战录音 */
export function submitChallengeApi(challengeId, audioBlob) {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  return request.post(`/api/community/challenges/${challengeId}/submit`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 获取排行榜 */
export function getLeaderboardApi(challengeId) {
  return request.get(`/api/community/challenges/${challengeId}/leaderboard`)
}

// ===== 话题讨论 =====

/** 获取帖子列表 */
export function getPostsApi() {
  return request.get('/api/community/posts')
}

/** 发帖 */
export function createPostApi(topic, content, groupId = null) {
  return request.post('/api/community/posts', { topic, content, group_id: groupId })
}

/** 切换点赞 */
export function toggleLikeApi(postId) {
  return request.post(`/api/community/posts/${postId}/like`)
}

/** 获取评论 */
export function getCommentsApi(postId) {
  return request.get(`/api/community/posts/${postId}/comments`)
}

/** 发表评论 */
export function addCommentApi(postId, content) {
  return request.post(`/api/community/posts/${postId}/comments`, { content })
}

// ===== 学习小组 =====

/** 获取小组列表 */
export function getGroupsApi() {
  return request.get('/api/community/groups')
}

/** 加入/退出小组 */
export function toggleGroupApi(groupId) {
  return request.post(`/api/community/groups/${groupId}/join`)
}

/** 创建小组 */
export function createGroupApi(data) {
  return request.post('/api/community/groups', data)
}

/** 获取小组详情 */
export function getGroupDetailApi(groupId) {
  return request.get(`/api/community/groups/${groupId}`)
}

/** 获取小组成员 */
export function getGroupMembersApi(groupId) {
  return request.get(`/api/community/groups/${groupId}/members`)
}

/** 获取小组帖子 */
export function getGroupPostsApi(groupId) {
  return request.get(`/api/community/groups/${groupId}/posts`)
}