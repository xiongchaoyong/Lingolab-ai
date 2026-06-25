import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getDailyChallengeApi,
  submitLevelApi,
  completeDailyApi,
  getDubbingContentApi,
  submitDubbingApi,
  getDubbingRecordsApi,
  getBadgesApi,
  getPointsApi,
} from '@/api/gamification'

export const useGamificationStore = defineStore('gamification', () => {
  // ===== 每日闯关 =====
  const dailyLevels = ref([])
  const dailyDate = ref('')
  const dailyCompleted = ref(false)
  const levelScores = ref({})
  const scoringLevel = ref(-1) // 正在评分的关卡
  const dailyLoading = ref(false)

  const currentLevel = computed(() => {
    const passed = Object.keys(levelScores.value).length
    return passed
  })

  const dailyPoints = computed(() => {
    let pts = 0
    Object.values(levelScores.value).forEach(s => {
      if (s >= 70) pts += 20
    })
    if (dailyCompleted.value) pts += 30
    return pts
  })

  async function fetchDailyChallenge() {
    dailyLoading.value = true
    try {
      const data = await getDailyChallengeApi()
      dailyLevels.value = data.levels || []
      dailyDate.value = data.date
      dailyCompleted.value = data.completed
      levelScores.value = data.level_scores || {}
    } catch {
      // 错误由拦截器统一处理
    } finally {
      dailyLoading.value = false
    }
  }

  async function submitLevel(audio, levelIndex) {
    scoringLevel.value = levelIndex
    try {
      const result = await submitLevelApi(audio, levelIndex + 1)
      levelScores.value = { ...levelScores.value, [levelIndex]: result.score }
      if (levelIndex >= 4 && result.passed) {
        dailyCompleted.value = true
      }
      return result
    } finally {
      scoringLevel.value = -1
    }
  }

  async function completeDailyChallenge() {
    const passed = Object.values(levelScores.value).filter(s => s >= 70).length
    const result = await completeDailyApi(passed)
    dailyCompleted.value = true
    return result
  }

  // ===== 配音挑战 =====
  const dubbingContent = ref([])
  const dubbingRecords = ref([])
  const dubbingLoading = ref(false)
  const dubbingScoring = ref(false)
  const dubbingResult = ref(null)

  async function fetchDubbingContent(difficulty = null) {
    dubbingLoading.value = true
    try {
      dubbingContent.value = await getDubbingContentApi(difficulty)
    } finally {
      dubbingLoading.value = false
    }
  }

  async function submitDubbing(audio, contentId) {
    dubbingScoring.value = true
    try {
      const result = await submitDubbingApi(audio, contentId)
      dubbingResult.value = result
      return result
    } finally {
      dubbingScoring.value = false
    }
  }

  function clearDubbingResult() {
    dubbingResult.value = null
  }

  async function fetchDubbingRecords(limit = 20) {
    dubbingRecords.value = await getDubbingRecordsApi(limit)
  }

  // ===== 勋章 & 积分 =====
  const badges = ref([])
  const points = ref({ total_points: 0, recent_records: [] })
  const badgesLoading = ref(false)

  async function fetchBadges() {
    badgesLoading.value = true
    try {
      badges.value = await getBadgesApi()
    } finally {
      badgesLoading.value = false
    }
  }

  async function fetchPoints() {
    points.value = await getPointsApi()
  }

  // ===== 返回 =====
  return {
    // 每日闯关
    dailyLevels, dailyDate, dailyCompleted, levelScores,
    scoringLevel, currentLevel, dailyPoints, dailyLoading,
    fetchDailyChallenge, submitLevel, completeDailyChallenge,
    // 配音挑战
    dubbingContent, dubbingRecords, dubbingLoading, dubbingScoring, dubbingResult,
    fetchDubbingContent, submitDubbing, clearDubbingResult, fetchDubbingRecords,
    // 勋章 & 积分
    badges, points, badgesLoading,
    fetchBadges, fetchPoints,
  }
})