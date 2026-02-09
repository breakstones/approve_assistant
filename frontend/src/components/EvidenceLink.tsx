/**
 * Evidence Link Component
 * Evidence 联动定位组件
 *
 * 增强证据点击体验，提供平滑滚动和高亮动画
 */
import { useState, useEffect, useRef, useCallback } from 'react'

export interface EvidenceLinkProps {
  /**
   * 证据数据
   */
  evidence: {
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

  /**
   * 点击回调
   */
  onClick?: (evidence: EvidenceLinkProps['evidence']) => void

  /**
   * 是否显示缩略引用
   */
  showQuote?: boolean

  /**
   * 引用文本最大长度
   */
  quoteMaxLength?: number

  /**
   * 是否处于激活状态
   */
  active?: boolean

  /**
   * 是否显示置信度
   */
  showConfidence?: boolean
}

export default function EvidenceLink({
  evidence,
  onClick,
  showQuote = true,
  quoteMaxLength = 100,
  active = false,
  showConfidence = true,
}: EvidenceLinkProps) {
  const handleClick = useCallback(() => {
    onClick?.(evidence)
  }, [evidence, onClick])

  // 截断引用文本
  const truncatedQuote =
    evidence.quote.length > quoteMaxLength
      ? evidence.quote.substring(0, quoteMaxLength) + '...'
      : evidence.quote

  return (
    <div
      className={`
        p-3 rounded-lg border transition-all cursor-pointer
        ${active
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-sm'
        }
      `}
      onClick={handleClick}
    >
      {/* 页码和置信度 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`
            px-2 py-0.5 text-xs font-medium rounded
            ${active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}
          `}>
            第 {evidence.page} 页
          </span>
          {evidence.confidence !== undefined && showConfidence && (
            <span className="text-xs text-gray-500">
              置信度: {Math.round(evidence.confidence * 100)}%
            </span>
          )}
        </div>

        {/* 激活指示器 */}
        {active && (
          <div className="flex items-center text-blue-600 text-xs">
            <span className="animate-pulse mr-1">●</span>
            <span>已定位</span>
          </div>
        )}
      </div>

      {/* 引用文本 */}
      {showQuote && (
        <p className="text-sm text-gray-700 leading-relaxed">
          {truncatedQuote}
        </p>
      )}

      {/* 点击提示 */}
      <div className={`
        mt-2 text-xs flex items-center transition-opacity
        ${active ? 'text-blue-600' : 'text-gray-500'}
      `}>
        <span>点击定位到原文</span>
        <svg
          className="w-3 h-3 ml-1"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </div>
  )
}

/**
 * Evidence Link 管理器 Hook
 * 管理 Evidence 联动定位的状态
 */
export interface UseEvidenceLinkResult {
  /**
   * 当前激活的证据 ID
   */
  activeEvidenceId: string | null

  /**
   * 处理证据点击
   */
  handleEvidenceClick: (evidence: EvidenceLinkProps['evidence']) => void

  /**
   * 清除激活状态
   */
  clearActiveEvidence: () => void
}

export function useEvidenceLink(
  onEvidenceClick?: (evidence: EvidenceLinkProps['evidence']) => void
): UseEvidenceLinkResult {
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleEvidenceClick = useCallback((evidence: EvidenceLinkProps['evidence']) => {
    // 设置新的激活证据
    setActiveEvidenceId(evidence.chunk_id)

    // 清除之前的定时器
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // 3秒后自动清除激活状态
    timeoutRef.current = setTimeout(() => {
      setActiveEvidenceId(null)
    }, 3000)

    // 调用外部回调
    onEvidenceClick?.(evidence)
  }, [onEvidenceClick])

  const clearActiveEvidence = useCallback(() => {
    setActiveEvidenceId(null)
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return {
    activeEvidenceId,
    handleEvidenceClick,
    clearActiveEvidence,
  }
}

/**
 * 证据列表组件
 * 使用 EvidenceLink 展示多个证据
 */
export interface EvidenceListProps {
  /**
   * 证据列表
   */
  evidences: EvidenceLinkProps['evidence'][]

  /**
   * 证据点击回调
   */
  onEvidenceClick?: (evidence: EvidenceLinkProps['evidence']) => void

  /**
   * 当前激活的证据 ID
   */
  activeEvidenceId?: string | null

  /**
   * 是否显示引用
   */
  showQuote?: boolean

  /**
   * 是否显示置信度
   */
  showConfidence?: boolean
}

export function EvidenceList({
  evidences,
  onEvidenceClick,
  activeEvidenceId = null,
  showQuote = true,
  showConfidence = true,
}: EvidenceListProps) {
  if (evidences.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        暂无相关证据
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {evidences.map((evidence, index) => (
        <EvidenceLink
          key={`${evidence.chunk_id}-${index}`}
          evidence={evidence}
          onClick={onEvidenceClick}
          active={activeEvidenceId === evidence.chunk_id}
          showQuote={showQuote}
          showConfidence={showConfidence}
        />
      ))}
    </div>
  )
}
