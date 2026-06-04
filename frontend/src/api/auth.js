import request from './index'

// 预留 API 接口，等后端开发后启用
export function loginApi(data) {
  return request.post('/api/auth/login', data)
}

export function registerApi(data) {
  return request.post('/api/auth/register', data)
}

export function getProfileApi() {
  return request.get('/api/auth/profile')
}
