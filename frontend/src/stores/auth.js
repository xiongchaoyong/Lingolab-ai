import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getProfileApi, updateProfileApi, uploadAvatarApi } from '@/api/auth'

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
    const res = await loginApi({ username, password })
    setToken(res.token)
    setUserInfo({
      id: res.user_id,
      username: res.username,
      role: 'learner',
      assessment_completed: res.assessment_completed,
      avatar: res.avatar,
    })
    return res
  }

  async function register(formData) {
    const res = await registerApi({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      age: formData.age,
      learning_goal: formData.learning_goal,
      interests: formData.interests,
    })
    setToken(res.token)
    setUserInfo({
      id: res.user_id,
      username: res.username,
      role: 'learner',
      age_group: res.age_group,
      assessment_completed: false,
    })
    return res
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  async function fetchProfile() {
    const res = await getProfileApi()
    setUserInfo({
      id: res.user_id,
      username: res.username,
      email: res.email,
      age: res.age,
      age_group: res.age_group,
      learning_goal: res.learning_goal,
      interests: res.interests,
      level_final: res.level_final,
      assessment_completed: res.assessment_completed,
      role: res.role,
      avatar: res.avatar,
    })
    return res
  }

  async function updateProfile(data) {
    const res = await updateProfileApi(data)
    if (userInfo.value) {
      userInfo.value.learning_goal = res.learning_goal
      userInfo.value.interests = res.interests
    }
    return res
  }

  async function uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await uploadAvatarApi(formData)
    if (userInfo.value) {
      userInfo.value.avatar = res.avatar_url
    }
    return res
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
    updateProfile,
    uploadAvatar,
  }
})