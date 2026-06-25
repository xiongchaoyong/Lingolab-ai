import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getChallengesApi,
  submitChallengeApi,
  getLeaderboardApi,
  getPostsApi,
  createPostApi,
  toggleLikeApi,
  getCommentsApi,
  addCommentApi,
  getGroupsApi,
  toggleGroupApi,
} from '@/api/community'

export const useCommunityStore = defineStore('community', () => {
  // ===== 语音挑战 =====
  const challenges = ref([])
  const leaderboard = ref([])
  const currentChallenge = ref(null)
  const challengesLoading = ref(false)

  async function fetchChallenges() {
    challengesLoading.value = true
    try {
      const result = await getChallengesApi()
      challenges.value = result.challenges || []
      if (challenges.value.length > 0) {
        currentChallenge.value = challenges.value[0]
      }
    } finally {
      challengesLoading.value = false
    }
  }

  async function submitChallenge(challengeId, audioBlob) {
    return await submitChallengeApi(challengeId, audioBlob)
  }

  async function fetchLeaderboard(challengeId) {
    const result = await getLeaderboardApi(challengeId)
    leaderboard.value = result.leaderboard || []
    return leaderboard.value
  }

  // ===== 话题讨论 =====
  const posts = ref([])
  const postsLoading = ref(false)

  async function fetchPosts() {
    postsLoading.value = true
    try {
      const result = await getPostsApi()
      posts.value = result.posts || []
    } finally {
      postsLoading.value = false
    }
  }

  async function createPost(topic, content) {
    const post = await createPostApi(topic, content)
    posts.value.unshift(post)
    return post
  }

  async function toggleLike(postId) {
    const result = await toggleLikeApi(postId)
    const post = posts.value.find(p => p.id === postId)
    if (post) {
      post.is_liked = result.liked
      post.likes_count = result.likes_count
    }
    return result
  }

  // ===== 评论 =====
  async function fetchComments(postId) {
    const result = await getCommentsApi(postId)
    return result.comments || []
  }

  async function addComment(postId, content) {
    const comment = await addCommentApi(postId, content)
    const post = posts.value.find(p => p.id === postId)
    if (post) {
      post.comments_count += 1
    }
    return comment
  }

  // ===== 学习小组 =====
  const groups = ref([])
  const groupsLoading = ref(false)

  async function fetchGroups() {
    groupsLoading.value = true
    try {
      const result = await getGroupsApi()
      groups.value = result.groups || []
    } finally {
      groupsLoading.value = false
    }
  }

  async function toggleGroup(groupId) {
    const result = await toggleGroupApi(groupId)
    const group = groups.value.find(g => g.id === groupId)
    if (group) {
      group.is_joined = result.joined
      group.member_count = result.member_count
    }
    return result
  }

  return {
    challenges, leaderboard, currentChallenge, challengesLoading,
    fetchChallenges, submitChallenge, fetchLeaderboard,
    posts, postsLoading, fetchPosts, createPost, toggleLike,
    fetchComments, addComment,
    groups, groupsLoading, fetchGroups, toggleGroup,
  }
})