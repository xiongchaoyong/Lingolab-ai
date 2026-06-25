import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getPredictionApi,
  setTargetScoreApi,
  checkAlertsApi,
  getNoticesApi,
  markNoticeReadApi,
  markAllNoticesReadApi,
  getUnreadCountApi,
} from '@/api/prediction'

export const usePredictionStore = defineStore('prediction', () => {
  // ===== 预测 =====
  const prediction = ref({
    current_score: 0,
    trend_slope: null,
    target_score: 85,
    predicted_days: null,
    predicted_date: null,
    trend: 'stable',
    message: '数据不足',
  })
  const predictionLoading = ref(false)

  async function fetchPrediction() {
    predictionLoading.value = true
    try {
      prediction.value = await getPredictionApi()
    } finally {
      predictionLoading.value = false
    }
  }

  async function updateTarget(score) {
    prediction.value = await setTargetScoreApi(score)
  }

  // ===== 预警 =====
  const alerts = ref([])
  const alertsLoading = ref(false)

  async function checkAlerts() {
    alertsLoading.value = true
    try {
      const result = await checkAlertsApi()
      alerts.value = result.alerts || []
    } finally {
      alertsLoading.value = false
    }
  }

  // ===== 通知 =====
  const notices = ref([])
  const unreadCount = ref(0)
  const noticesLoading = ref(false)

  async function fetchNotices(unreadOnly = false) {
    noticesLoading.value = true
    try {
      const result = await getNoticesApi(unreadOnly)
      notices.value = result.notices || []
      unreadCount.value = result.unread_count || 0
    } finally {
      noticesLoading.value = false
    }
  }

  async function markRead(id) {
    await markNoticeReadApi(id)
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function markAllRead() {
    await markAllNoticesReadApi()
    unreadCount.value = 0
  }

  async function fetchUnreadCount() {
    try {
      const result = await getUnreadCountApi()
      unreadCount.value = result.unread_count || 0
    } catch {
      // 静默失败
    }
  }

  return {
    prediction, predictionLoading,
    alerts, alertsLoading,
    notices, unreadCount, noticesLoading,
    fetchPrediction, updateTarget,
    checkAlerts, fetchNotices,
    markRead, markAllRead, fetchUnreadCount,
  }
})