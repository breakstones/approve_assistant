/**
 * Explainability API
 * 追问与解释 API
 */
import { apiClient } from './client'

// 解释类型定义
export interface ExplainRequest {
  review_id: string
  result_id: string
  question: string
  session_id?: string
}

export interface ExplainResponse {
  session_id: string
  message_id: string
  answer: string
  reasoning: string
  evidence_references: Array<{
    chunk_id: string
    quote: string
    page: number
    bbox?: {
      x1: number
      y1: number
      x2: number
      y2: number
    }
    relevance: string
  }>
  confidence: 'high' | 'medium' | 'low'
  limitations: string[]
  timestamp: string
}

export interface ConversationMessage {
  message_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ConversationHistory {
  session_id: string
  review_id: string
  result_id: string
  messages: ConversationMessage[]
  created_at: string
  last_updated: string
}

export interface ExplainSession {
  session_id: string
  review_id: string
  result_id: string
  message_count: number
  created_at: string
  last_updated: string
}

// 解释 API 方法
export const explainApi = {
  /**
   * 发起追问
   */
  ask: async (request: ExplainRequest): Promise<ExplainResponse> => {
    return apiClient.post('/explain', request)
  },

  /**
   * 获取对话历史
   */
  getHistory: async (sessionId: string): Promise<ConversationHistory> => {
    return apiClient.get(`/explain/${sessionId}/history`)
  },

  /**
   * 列出会话
   */
  listSessions: async (params?: {
    review_id?: string
    limit?: number
  }): Promise<ExplainSession[]> => {
    return apiClient.get('/explain/sessions', { params })
  },

  /**
   * 删除会话
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    return apiClient.delete(`/explain/${sessionId}`)
  },
}
