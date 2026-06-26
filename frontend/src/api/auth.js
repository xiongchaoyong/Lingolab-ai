import request from './index'

export function loginApi(data) {
  return request.post('/api/auth/login', data)
}

export function registerApi(data) {
  return request.post('/api/auth/register', data)
}

export function getProfileApi() {
  return request.get('/api/auth/profile')
}

export function updateProfileApi(data) {
  return request.put('/api/auth/profile', data)
}

export function refreshTokenApi() {
  return request.post('/api/auth/token/refresh')
}

export function uploadAvatarApi(formData) {
  return request.post('/api/auth/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
