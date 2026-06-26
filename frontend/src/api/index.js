import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  // Content-Type 由各请求自行设置，FormData 上传需要 multipart/form-data
})

// 是否正在刷新 token
let isRefreshing = false
// 等待刷新的请求队列
let pendingRequests = []

// 请求拦截器 — 自动附加 JWT token
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 — 统一错误处理 + Token 自动刷新
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      const { status, data } = error.response

      // 401 且非刷新请求本身 → 尝试刷新 Token
      if (status === 401 && !originalRequest._retry && !originalRequest.url.includes('/token/refresh')) {
        if (isRefreshing) {
          // 已在刷新中，将请求加入队列等待
          return new Promise((resolve) => {
            pendingRequests.push(() => resolve(request(originalRequest)))
          })
        }

        isRefreshing = true
        originalRequest._retry = true

        try {
          const authStore = useAuthStore()
          // 直接用 axios 发送刷新请求，避免循环拦截
          const resp = await axios.post(
            `${import.meta.env.VITE_API_BASE_URL}/api/auth/token/refresh`,
            {},
            { headers: { Authorization: `Bearer ${authStore.token}` } }
          )
          const newToken = resp.data.token
          authStore.setToken(newToken)

          // 重试原始请求
          originalRequest.headers.Authorization = `Bearer ${newToken}`

          // 执行队列中的等待请求
          pendingRequests.forEach((cb) => cb())
          pendingRequests = []

          return request(originalRequest)
        } catch (refreshError) {
          // 刷新失败，清除登录状态
          const authStore = useAuthStore()
          authStore.logout()
          ElMessage.error('登录已过期，请重新登录')
          pendingRequests = []
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }

      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          useAuthStore().logout()
          break
        case 403:
          ElMessage.error('没有访问权限')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接异常')
    }
    return Promise.reject(error)
  }
)

export default request
