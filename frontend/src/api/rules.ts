/**
 * Rules API
 * 规则管理 API
 */
import { apiClient } from './client'

// 规则类型定义
export interface Rule {
  rule_id: string
  name: string
  category: string
  intent: string
  type: 'numeric_constraint' | 'text_contains' | 'prohibition' | 'requirement'
  params: Record<string, unknown>
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
  retrieval_tags: string[]
  enabled: boolean
  created_at?: string
  updated_at?: string
}

export interface RuleCreateRequest {
  name: string
  category: string
  intent: string
  type: Rule['type']
  params: Record<string, unknown>
  risk_level: Rule['risk_level']
  retrieval_tags: string[]
  enabled?: boolean
}

export interface RuleListResponse {
  rules: Rule[]
  total: number
}

// 规则 API 方法
export const rulesApi = {
  /**
   * 获取规则列表
   */
  list: async (params?: {
    category?: string
    risk_level?: string
    type?: string
    enabled_only?: boolean
    limit?: number
  }): Promise<Rule[]> => {
    return apiClient.get('/rules', { params })
  },

  /**
   * 获取单个规则
   */
  get: async (ruleId: string): Promise<Rule> => {
    return apiClient.get(`/rules/${ruleId}`)
  },

  /**
   * 创建规则
   */
  create: async (rule: RuleCreateRequest): Promise<Rule> => {
    return apiClient.post('/rules', rule)
  },

  /**
   * 更新规则
   */
  update: async (ruleId: string, rule: Partial<RuleCreateRequest>): Promise<Rule> => {
    return apiClient.put(`/rules/${ruleId}`, rule)
  },

  /**
   * 删除规则（软删除）
   */
  delete: async (ruleId: string): Promise<void> => {
    return apiClient.delete(`/rules/${ruleId}`)
  },

  /**
   * 批量创建规则
   */
  bulkCreate: async (rules: RuleCreateRequest[]): Promise<{ created: number; failed: number }> => {
    return apiClient.post('/rules/bulk', { rules })
  },

  /**
   * 解析自然语言规则
   */
  parse: async (description: string): Promise<Rule> => {
    return apiClient.post('/rules/parse', { description })
  },
}
