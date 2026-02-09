/**
 * Documents API
 * 文档管理 API
 */
import { apiClient } from './client'

// 文档类型定义
export type DocumentStatus = 'UPLOADED' | 'PROCESSING' | 'READY' | 'ERROR' | 'REVIEWING' | 'REVIEWED'

export interface Document {
  doc_id: string
  filename: string
  file_type: 'pdf' | 'docx'
  file_size: number
  status: DocumentStatus
  page_count?: number
  chunk_count?: number
  error_message?: string
  doc_metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface DocumentUploadResponse {
  doc_id: string
  filename: string
  status: DocumentStatus
  message: string
}

export interface DocumentStatusResponse {
  doc_id: string
  filename: string
  status: DocumentStatus
  progress: number
  page_count?: number
  chunk_count?: number
  error_message?: string
  created_at: string
  updated_at: string
}

// 文档 API 方法
export const documentsApi = {
  /**
   * 上传文档
   */
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<DocumentUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
  },

  /**
   * 获取文档状态
   */
  getStatus: async (docId: string): Promise<DocumentStatusResponse> => {
    return apiClient.get(`/documents/${docId}/status`)
  },

  /**
   * 获取文档列表
   */
  list: async (params?: {
    status?: DocumentStatus
    limit?: number
    offset?: number
  }): Promise<Document[]> => {
    return apiClient.get('/documents', { params })
  },

  /**
   * 获取单个文档
   */
  get: async (docId: string): Promise<Document> => {
    return apiClient.get(`/documents/${docId}`)
  },

  /**
   * 删除文档
   */
  delete: async (docId: string): Promise<void> => {
    return apiClient.delete(`/documents/${docId}`)
  },
}
