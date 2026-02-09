/**
 * Review API
 * 审查任务 API
 */
import { apiClient } from './client'

// 审查类型定义
export type ReviewStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface Evidence {
  chunk_id: string
  quote: string
  page: number
  bbox?: {
    x1: number
    y1: number
    x2: number
    y2: number
  }
  confidence?: number
}

export interface ReviewResult {
  rule_id: string
  rule_name: string
  status: 'PASS' | 'RISK' | 'MISSING'
  reason: string
  evidence: Evidence[]
  confidence: number
  suggestion?: string
}

export interface ReviewStartRequest {
  doc_id: string
  rule_ids?: string[]
  rules_filter?: {
    category?: string
    risk_level?: string
    type?: string
  }
}

export interface ReviewStartResponse {
  review_id: string
  doc_id: string
  total_rules: number
  status: ReviewStatus
  message: string
}

export interface ReviewStatusResponse {
  review_id: string
  doc_id: string
  status: ReviewStatus
  total_rules: number
  completed_rules: number
  progress: number
  started_at?: string
  completed_at?: string
  error?: string
}

export interface ReviewResultsResponse {
  review_id: string
  doc_id: string
  status: ReviewStatus
  results: ReviewResult[]
  summary: {
    total: number
    pass: number
    risk: number
    missing: number
    failed: number
  }
  started_at?: string
  completed_at?: string
  error?: string
}

export interface ReviewTask {
  review_id: string
  doc_id: string
  rule_ids: string[]
  status: ReviewStatus
  started_at?: string
  completed_at?: string
  error?: string
}

// 审查 API 方法
export const reviewApi = {
  /**
   * 启动审查
   */
  start: async (request: ReviewStartRequest): Promise<ReviewStartResponse> => {
    return apiClient.post('/review/start', request)
  },

  /**
   * 获取审查状态
   */
  getStatus: async (reviewId: string): Promise<ReviewStatusResponse> => {
    return apiClient.get(`/review/${reviewId}/status`)
  },

  /**
   * 获取审查结果
   */
  getResults: async (reviewId: string): Promise<ReviewResultsResponse> => {
    return apiClient.get(`/review/${reviewId}/results`)
  },

  /**
   * 列出审查任务
   */
  list: async (params?: {
    status?: ReviewStatus
    doc_id?: string
    limit?: number
  }): Promise<ReviewTask[]> => {
    return apiClient.get('/review', { params })
  },

  /**
   * 取消审查任务
   */
  cancel: async (reviewId: string): Promise<void> => {
    return apiClient.delete(`/review/${reviewId}`)
  },
}
