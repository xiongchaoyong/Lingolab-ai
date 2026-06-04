import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Mock 题目数据：10题混合排列
const MOCK_QUESTIONS = [
  { id: 1, type: 'listening', difficulty: 'B1', content: '听力：What does the woman mean? (Audio clip about weekend plans)', options: ['A. She likes to travel', 'B. She works at a hospital', 'C. She is studying medicine', 'D. She wants to be a teacher'], answer: 'A' },
  { id: 2, type: 'reading', difficulty: 'B1', content: 'Reading: Choose the best word to fill in the blank.\n\n"The company has _____ its profits by 20% this year."', options: ['A. increased', 'B. decreased', 'C. maintained', 'D. predicted'], answer: 'A' },
  { id: 3, type: 'speaking', difficulty: 'B1', content: 'Speaking: Describe your favorite food. What is it? Why do you like it? How often do you eat it?', options: [], answer: null },
  { id: 4, type: 'grammar', difficulty: 'A2', content: 'Grammar: Choose the correct sentence.', options: ['A. She don\'t like coffee', 'B. She doesn\'t likes coffee', 'C. She doesn\'t like coffee', 'D. She not like coffee'], answer: 'C' },
  { id: 5, type: 'listening', difficulty: 'A2', content: '听力：Where does this conversation probably take place? (Audio clip about ordering food)', options: ['A. In a library', 'B. In a restaurant', 'C. In a hospital', 'D. In a classroom'], answer: 'B' },
  { id: 6, type: 'reading', difficulty: 'B2', content: 'Reading: What is the main idea of the passage?\n\n"Climate change has become one of the most pressing issues of our time. Scientists warn that rising temperatures could lead to severe consequences including extreme weather events, sea level rise, and biodiversity loss."', options: ['A. Weather is unpredictable', 'B. Climate change poses serious threats', 'C. Scientists disagree on climate issues', 'D. Biodiversity is decreasing naturally'], answer: 'B' },
  { id: 7, type: 'speaking', difficulty: 'B2', content: 'Speaking: Talk about a memorable trip you have taken. Where did you go? Who did you go with? What made it special?', options: [], answer: null },
  { id: 8, type: 'grammar', difficulty: 'B1', content: 'Grammar: "If I _____ rich, I would travel around the world."', options: ['A. am', 'B. was', 'C. were', 'D. be'], answer: 'C' },
  { id: 9, type: 'listening', difficulty: 'B2', content: '听力：What is the speaker\'s attitude toward the proposal? (Audio clip about a business plan)', options: ['A. Enthusiastic', 'B. Skeptical', 'C. Neutral', 'D. Confused'], answer: 'B' },
  { id: 10, type: 'reading', difficulty: 'B1', content: 'Reading: According to the text, which statement is TRUE?\n\n"Regular exercise has been shown to improve both physical and mental health. Studies indicate that even 30 minutes of moderate activity per day can reduce the risk of heart disease by up to 30%."', options: ['A. Exercise only benefits physical health', 'B. 30 minutes of daily exercise can lower heart disease risk', 'C. Mental health is unrelated to exercise', 'D. Only intense exercise provides health benefits'], answer: 'B' },
]

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
  const questions = ref(MOCK_QUESTIONS)
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
  function startAssessment() {
    // 尝试从 localStorage 恢复
    const saved = localStorage.getItem('assessment_progress')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        currentIndex.value = data.currentIndex || 0
        answers.value = data.answers || {}
        startTime.value = data.startTime || Date.now()
        return
      } catch {}
    }
    currentIndex.value = 0
    answers.value = {}
    startTime.value = Date.now()
    isCompleted.value = false
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
      currentIndex: currentIndex.value,
      answers: answers.value,
      startTime: startTime.value,
    }))
  }

  function completeAssessment() {
    isCompleted.value = true
    localStorage.removeItem('assessment_progress')

    // 生成模拟测评报告
    const dimensionScores = {
      listening: randomScore(50, 95),
      speaking: randomScore(40, 90),
      reading: randomScore(55, 95),
      grammar: randomScore(45, 90),
    }

    const overall = Math.round(
      Object.values(dimensionScores).reduce((a, b) => a + b, 0) / 4
    )

    const cefrLevel = getCEFR(overall)
    const weakness = Object.entries(dimensionScores)
      .sort((a, b) => a[1] - b[1])[0]

    report.value = {
      overall,
      cefrLevel,
      dimensionScores,
      weakness: {
        dimension: weakness[0],
        score: weakness[1],
        label: DIMENSION_LABELS[weakness[0]],
        suggestion: getSuggestion(weakness[0]),
      },
      duration: Math.round((Date.now() - startTime.value) / 1000),
    }
  }

  function resetAssessment() {
    currentIndex.value = 0
    answers.value = {}
    startTime.value = null
    isCompleted.value = false
    report.value = null
    localStorage.removeItem('assessment_progress')
  }

  return {
    questions, currentIndex, answers, startTime, isCompleted, report,
    currentQuestion, totalQuestions, progress, isSpeakingQuestion, isLastQuestion,
    typeLabel, difficultyColor,
    startAssessment, saveAnswer, nextQuestion, completeAssessment, resetAssessment,
  }
})

// 工具函数
const DIMENSION_LABELS = {
  listening: '听力理解', speaking: '口语表达',
  reading: '阅读理解', grammar: '语法选择',
}

function randomScore(min, max) {
  return Math.round(min + Math.random() * (max - min))
}

function getCEFR(score) {
  if (score <= 20) return { level: 'A1', label: '入门' }
  if (score <= 40) return { level: 'A2', label: '基础' }
  if (score <= 60) return { level: 'B1', label: '中级' }
  if (score <= 80) return { level: 'B2', label: '中高级' }
  if (score <= 95) return { level: 'C1', label: '高级' }
  return { level: 'C2', label: '精通' }
}

function getSuggestion(dimension) {
  const suggestions = {
    listening: '建议每天听15分钟英语播客或新闻，逐步提升听力理解能力',
    speaking: '建议多进行口语练习，可以先从简单的自我介绍和日常话题开始',
    reading: '建议每天阅读一篇英语短文，注意积累词汇和理解文章结构',
    grammar: '建议系统复习基础语法知识，重点关注时态和句型结构',
  }
  return suggestions[dimension] || ''
}
