/**
 * API Client Configuration
 * API 客户端配置
 */
import axios from 'axios'

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token 等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// API 端点类型定义
export interface ApiError {
  detail: string
  status?: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

// 导出 API 基础 URL
export { API_BASE_URL }
