import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // ---- state ----
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  // ---- getters ----
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => userInfo.value?.role || 'learner')

  // ---- actions ----
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
  }

  async function login(username, password) {
    // TODO: 对接后端 API
    // const res = await authApi.login({ username, password })
    // setToken(res.token)
    // setUserInfo(res.user)

    // 前端阶段：模拟登录
    setToken('mock-jwt-token')
    setUserInfo({
      id: 1,
      username,
      role: 'learner',
      age_group: '大学生',
      cefr_level: null,
    })
  }

  async function register(formData) {
    // TODO: 对接后端 API
    // const res = await authApi.register(formData)
    // setToken(res.token)
    // setUserInfo(res.user)

    // 前端阶段：模拟注册
    setToken('mock-jwt-token')
    setUserInfo({
      id: 1,
      username: formData.username,
      role: 'learner',
      age_group: formData.age_group,
      learning_goal: formData.learning_goal,
    })
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  async function fetchProfile() {
    // TODO: 对接后端 API
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    userRole,
    setToken,
    setUserInfo,
    login,
    register,
    logout,
    fetchProfile,
  }
})
