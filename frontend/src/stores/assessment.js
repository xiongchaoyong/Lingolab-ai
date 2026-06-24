import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { startAssessmentApi, answerQuestionApi, completeAssessmentApi } from '@/api/assessment'
import { useAuthStore } from '@/stores/auth'

const TYPE_LABELS = {
  listening: '听力理解',
  reading: '阅读理解',
  grammar: '语法选择',
  speaking: '口语表达',
}

const DIFFICULTY_COLORS = {
  A1: 'success', A2: 'success',
  B1: 'warning', B2: 'warning',
  C1: 'danger', C2: 'danger',
}

export const useAssessmentStore = defineStore('assessment', () => {
  const sessionId = ref(null)
  const currentQuestion = ref(null)
  const answeredCount = ref(0)
  const totalQuestions = ref(10)
  const currentDifficulty = ref('B1')
  const startTime = ref(null)
  const isCompleted = ref(false)
  const report = ref(null)
  const isScoring = ref(false)

  // ------- getters -------
  const progress = computed(() => (answeredCount.value / totalQuestions.value) * 100)
  const isSpeakingQuestion = computed(() => currentQuestion.value?.type === 'speaking')
  const isLastQuestion = computed(() => answeredCount.value >= totalQuestions.value - 1)

  const typeLabel = computed(() => TYPE_LABELS[currentQuestion.value?.type] || '')
  const difficultyColor = computed(() => DIFFICULTY_COLORS[currentQuestion.value?.difficulty] || 'info')

  // ------- actions -------
  async function startAssessment() {
    // 尝试从 localStorage 恢复
    const saved = localStorage.getItem('assessment_progress')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        if (data.sessionId && data.currentQuestion) {
          sessionId.value = data.sessionId
          currentQuestion.value = data.currentQuestion
          answeredCount.value = data.answeredCount || 0
          totalQuestions.value = data.totalQuestions || 10
          currentDifficulty.value = data.currentDifficulty || 'B1'
          startTime.value = data.startTime || Date.now()
          return
        }
      } catch {}
    }

    // 从后端获取第一题
    const res = await startAssessmentApi()
    sessionId.value = res.session_id
    currentQuestion.value = res.question
    totalQuestions.value = res.total_questions
    currentDifficulty.value = res.current_difficulty
    answeredCount.value = 0
    startTime.value = Date.now()
    isCompleted.value = false
    saveProgress()
  }

  async function submitAndAdvance(answer, audioBlob = null, mimeType = null) {
    isScoring.value = true
    try {
      const res = await answerQuestionApi(
        sessionId.value,
        currentQuestion.value.id,
        answer,
        audioBlob,
        mimeType,
      )

      answeredCount.value++
      currentDifficulty.value = res.current_difficulty

      if (res.complete) {
        // 全部答完 → 调用 complete 获取报告
        await finishAssessment()
        return
      }

      currentQuestion.value = res.next_question
      saveProgress()
    } finally {
      isScoring.value = false
    }
  }

  async function finishAssessment() {
    const res = await completeAssessmentApi(sessionId.value)

    report.value = {
      overall: res.overall,
      cefrLevel: res.cefr_level,
      dimensionScores: res.dimension_scores,
      weakness: res.weakness,
      duration: res.duration,
    }

    // 同步更新 authStore，标记测评已完成
    const authStore = useAuthStore()
    if (authStore.userInfo) {
      authStore.userInfo.assessment_completed = true
    }

    isCompleted.value = true
    localStorage.removeItem('assessment_progress')
  }

  function saveProgress() {
    localStorage.setItem('assessment_progress', JSON.stringify({
      sessionId: sessionId.value,
      currentQuestion: currentQuestion.value,
      answeredCount: answeredCount.value,
      totalQuestions: totalQuestions.value,
      currentDifficulty: currentDifficulty.value,
      startTime: startTime.value,
    }))
  }

  function resetAssessment() {
    sessionId.value = null
    currentQuestion.value = null
    answeredCount.value = 0
    totalQuestions.value = 10
    currentDifficulty.value = 'B1'
    startTime.value = null
    isCompleted.value = false
    report.value = null
    isScoring.value = false
    localStorage.removeItem('assessment_progress')
  }

  return {
    sessionId, currentQuestion, answeredCount, totalQuestions, currentDifficulty,
    startTime, isCompleted, report, isScoring,
    progress, isSpeakingQuestion, isLastQuestion,
    typeLabel, difficultyColor,
    startAssessment, submitAndAdvance, finishAssessment, resetAssessment, saveProgress,
  }
})