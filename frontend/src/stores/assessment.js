import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { startAssessmentApi, submitAssessmentApi } from '@/api/assessment'
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
  const questions = ref([])
  const currentIndex = ref(0)
  const answers = ref({})
  const startTime = ref(null)
  const isCompleted = ref(false)
  const report = ref(null)

  // ------- getters -------
  const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
  const totalQuestions = computed(() => questions.value.length)
  const progress = computed(() => ((currentIndex.value) / totalQuestions.value) * 100)
  const isSpeakingQuestion = computed(() => currentQuestion.value?.type === 'speaking')
  const isLastQuestion = computed(() => currentIndex.value >= totalQuestions.value - 1)

  const typeLabel = computed(() => TYPE_LABELS[currentQuestion.value?.type] || '')
  const difficultyColor = computed(() => DIFFICULTY_COLORS[currentQuestion.value?.difficulty] || 'info')

  // ------- actions -------
  async function startAssessment() {
    // 尝试从 localStorage 恢复
    const saved = localStorage.getItem('assessment_progress')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        sessionId.value = data.sessionId
        questions.value = data.questions || []
        currentIndex.value = data.currentIndex || 0
        answers.value = data.answers || {}
        startTime.value = data.startTime || Date.now()
        if (questions.value.length > 0) return
      } catch {}
    }

    // 从后端获取题目
    const res = await startAssessmentApi()
    sessionId.value = res.session_id
    questions.value = res.questions
    currentIndex.value = 0
    answers.value = {}
    startTime.value = Date.now()
    isCompleted.value = false
    saveProgress()
  }

  function saveAnswer(answer) {
    answers.value[currentQuestion.value.id] = answer
    saveProgress()
  }

  function nextQuestion() {
    if (isLastQuestion.value) {
      completeAssessment()
      return
    }
    currentIndex.value++
    saveProgress()
  }

  function saveProgress() {
    localStorage.setItem('assessment_progress', JSON.stringify({
      sessionId: sessionId.value,
      questions: questions.value,
      currentIndex: currentIndex.value,
      answers: answers.value,
      startTime: startTime.value,
    }))
  }

  async function completeAssessment() {
    // 构建提交格式: [{question_id, answer}, ...]
    const answerList = questions.value.map(q => ({
      question_id: q.id,
      answer: answers.value[q.id] || null,
    }))

    const res = await submitAssessmentApi(sessionId.value, answerList)

    // 映射后端 snake_case → 前端 camelCase
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

  function resetAssessment() {
    sessionId.value = null
    currentIndex.value = 0
    answers.value = {}
    startTime.value = null
    isCompleted.value = false
    report.value = null
    localStorage.removeItem('assessment_progress')
  }

  return {
    sessionId, questions, currentIndex, answers, startTime, isCompleted, report,
    currentQuestion, totalQuestions, progress, isSpeakingQuestion, isLastQuestion,
    typeLabel, difficultyColor,
    startAssessment, saveAnswer, nextQuestion, completeAssessment, resetAssessment,
  }
})