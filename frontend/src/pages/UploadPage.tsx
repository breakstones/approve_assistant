/**
 * Upload Page
 * 文档上传页面
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { documentsApi, type DocumentStatus } from '../api'

// 允许的文件类型
const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

// 文件大小限制 (50MB)
const MAX_FILE_SIZE = 50 * 1024 * 1024

interface UploadState {
  file: File | null
  uploading: boolean
  progress: number
  documentId: string | null
  status: DocumentStatus | null
  error: string | null
}

export default function UploadPage() {
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    documentId: null,
    status: null,
    error: null,
  })
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 处理文件选择
  const handleFileSelect = useCallback((file: File) => {
    // 验证文件类型
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setUploadState((prev) => ({
        ...prev,
        error: `不支持的文件类型: ${file.type}。仅支持 PDF 和 DOCX 文件。`,
      }))
      return
    }

    // 验证文件大小
    if (file.size > MAX_FILE_SIZE) {
      setUploadState((prev) => ({
        ...prev,
        error: `文件过大: ${(file.size / 1024 / 1024).toFixed(2)}MB。最大支持 50MB。`,
      }))
      return
    }

    // 清除之前的错误
    setUploadState({
      file,
      uploading: false,
      progress: 0,
      documentId: null,
      status: null,
      error: null,
    })
  }, [])

  // 处理文件输入变化
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  // 处理拖拽事件
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  // 轮询文档状态
  const startPollingStatus = useCallback((docId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await documentsApi.getStatus(docId)

        setUploadState((prev) => ({
          ...prev,
          status: status.status,
        }))

        // 如果处理完成或失败，停止轮询
        if (status.status === 'READY' || status.status === 'ERROR') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }

          if (status.status === 'ERROR') {
            setUploadState((prev) => ({
              ...prev,
              error: status.error_message || '文档处理失败',
              uploading: false,
            }))
          } else {
            setUploadState((prev) => ({
              ...prev,
              uploading: false,
              progress: 100,
            }))
          }
        }
      } catch (error) {
        console.error('Failed to poll document status:', error)
      }
    }, 2000) // 每2秒轮询一次
  }, [])

  // 停止轮询
  const stopPollingStatus = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  // 开始上传
  const handleUpload = async () => {
    if (!uploadState.file) return

    setUploadState((prev) => ({
      ...prev,
      uploading: true,
      progress: 0,
      error: null,
    }))

    try {
      const response = await documentsApi.upload(uploadState.file, (progress) => {
        setUploadState((prev) => ({
          ...prev,
          progress,
        }))
      })

      setUploadState((prev) => ({
        ...prev,
        documentId: response.doc_id,
        status: response.status,
      }))

      // 开始轮询处理状态
      if (response.status === 'PROCESSING' || response.status === 'UPLOADED') {
        startPollingStatus(response.doc_id)
      } else if (response.status === 'READY') {
        setUploadState((prev) => ({
          ...prev,
          uploading: false,
          progress: 100,
        }))
      }
    } catch (error) {
      setUploadState((prev) => ({
        ...prev,
        uploading: false,
        error: error instanceof Error ? error.message : '上传失败',
      }))
    }
  }

  // 重置上传状态
  const handleReset = () => {
    stopPollingStatus()
    setUploadState({
      file: null,
      uploading: false,
      progress: 0,
      documentId: null,
      status: null,
      error: null,
    })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 组件卸载时清除轮询
  useEffect(() => {
    return () => {
      stopPollingStatus()
    }
  }, [stopPollingStatus])

  // 获取状态描述
  const getStatusDescription = (status: DocumentStatus | null): string => {
    switch (status) {
      case 'UPLOADED':
        return '已上传，等待处理...'
      case 'PROCESSING':
        return '正在处理文档...'
      case 'READY':
        return '处理完成，可以开始审核'
      case 'ERROR':
        return '处理失败'
      case 'REVIEWING':
        return '审核中...'
      case 'REVIEWED':
        return '审核完成'
      default:
        return ''
    }
  }

  // 获取状态颜色
  const getStatusColor = (status: DocumentStatus | null): string => {
    switch (status) {
      case 'UPLOADED':
      case 'PROCESSING':
        return 'text-yellow-600'
      case 'READY':
      case 'REVIEWED':
        return 'text-green-600'
      case 'ERROR':
        return 'text-red-600'
      case 'REVIEWING':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">上传文档</h1>
        <p className="text-gray-600">支持 PDF 和 DOCX 格式的合同文档，最大 50MB</p>
      </div>

      {/* 上传区域 */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-colors
          ${dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${uploadState.file ? 'border-green-500 bg-green-50' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {!uploadState.file ? (
          <>
            <svg
              className="mx-auto h-12 w-12 text-gray-400 mb-4"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="text-lg text-gray-600 mb-2">拖拽文件到此处，或点击选择文件</p>
            <p className="text-sm text-gray-500 mb-4">支持 PDF、DOCX 格式</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              选择文件
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileInputChange}
            />
          </>
        ) : (
          <div>
            <svg
              className="mx-auto h-12 w-12 text-green-500 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-lg font-medium text-gray-900 mb-1">
              {uploadState.file.name}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              {(uploadState.file.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <button
              onClick={handleReset}
              className="text-red-600 hover:text-red-700 text-sm"
            >
              重新选择
            </button>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {uploadState.error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{uploadState.error}</p>
        </div>
      )}

      {/* 上传按钮 */}
      {uploadState.file && !uploadState.uploading && !uploadState.documentId && (
        <div className="mt-4 text-center">
          <button
            onClick={handleUpload}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            开始上传
          </button>
        </div>
      )}

      {/* 上传进度 */}
      {uploadState.uploading && (
        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>上传中...</span>
            <span>{uploadState.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadState.progress}%` }}
            />
          </div>
          {uploadState.status && (
            <p className={`mt-2 text-sm ${getStatusColor(uploadState.status)}`}>
              {getStatusDescription(uploadState.status)}
            </p>
          )}
        </div>
      )}

      {/* 上传完成 */}
      {uploadState.documentId && uploadState.status === 'READY' && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-600 font-medium mb-2">上传成功！</p>
          <p className="text-sm text-gray-600 mb-4">文档已准备就绪，可以开始审核。</p>
          <div className="flex gap-3">
            <button
              onClick={() => (window.location.href = `/review/${uploadState.documentId}`)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              开始审核
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm"
            >
              上传新文档
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
