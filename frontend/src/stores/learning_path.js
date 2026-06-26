import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getDailyTasksApi,
  skipTaskApi,
  replaceTaskApi,
  adjustDifficultyApi,
  getHistoryApi,
  getProfileSummaryApi,
} from '@/api/learning_path'

export const useLearningPathStore = defineStore('learning_path', () => {
  const tasks = ref([])
  const progress = ref({ done: 0, total: 0 })
  const taskDate = ref('')
  const historyRecords = ref([])
  const loading = ref(false)
  const profileSummary = ref(null)

  const isAllDone = computed(() => progress.value.done >= progress.value.total && progress.value.total > 0)

  async function fetchDailyTasks() {
    loading.value = true
    try {
      const res = await getDailyTasksApi()
      tasks.value = res.tasks || []
      progress.value = res.progress || { done: 0, total: 0 }
      taskDate.value = res.date || ''
    } catch {
      // 错误已在拦截器处理
    } finally {
      loading.value = false
    }
  }

  async function skipTask(taskId, reason = null) {
    const res = await skipTaskApi(taskId, reason)
    if (res.status === 'ok') {
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx !== -1) {
        tasks.value[idx].status = 'skipped'
      }
    }
  }

  async function replaceTask(taskId) {
    const res = await replaceTaskApi(taskId)
    if (res.status === 'ok' && res.task) {
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx !== -1) {
        tasks.value[idx] = res.task
      }
    }
  }

  async function adjustDifficulty(taskId, direction) {
    const res = await adjustDifficultyApi(taskId, direction)
    if (res.status === 'ok' && res.task) {
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx !== -1) {
        tasks.value[idx].difficulty = res.task.difficulty
      }
    }
  }

  async function fetchHistory(days = 7) {
    const res = await getHistoryApi(days)
    historyRecords.value = res.records || []
  }

  async function fetchProfileSummary() {
    try {
      const res = await getProfileSummaryApi()
      profileSummary.value = res
    } catch {
      profileSummary.value = null
    }
  }

  return {
    tasks, progress, taskDate, historyRecords, loading, isAllDone, profileSummary,
    fetchDailyTasks, skipTask, replaceTask, adjustDifficulty, fetchHistory, fetchProfileSummary,
  }
})