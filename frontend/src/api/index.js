import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          localStorage.removeItem('access_token')
          window.location.href = '/#/login'
          ElMessage.error('登录已过期，请重新登录')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        case 413:
          ElMessage.error('文件过大')
          break
        case 400:
          ElMessage.error(data.detail || '请求参数错误')
          break
        default:
          break
      }
    }
    return Promise.reject(error)
  }
)

export default api
