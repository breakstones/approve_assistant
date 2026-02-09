/**
 * Review Layout Component
 * 双屏审核布局组件
 *
 * 左侧：审核结果列表
 * 右侧：文档预览
 * 中间：可拖拽调整宽度的分隔条
 */
import { useState, useRef, useCallback, useEffect, ReactNode } from 'react'

interface ReviewLayoutProps {
  /**
   * 左侧面板内容（审核结果）
   */
  leftPanel: ReactNode

  /**
   * 右侧面板内容（文档预览）
   */
  rightPanel: ReactNode

  /**
   * 初始左侧面板宽度百分比（0-100）
   */
  initialLeftPercent?: number

  /**
   * 最小左侧面板宽度百分比
   */
  minLeftPercent?: number

  /**
   * 最大左侧面板宽度百分比
   */
  maxLeftPercent?: number

  /**
   * 分隔条宽度（像素）
   */
  separatorWidth?: number

  /**
   * 是否禁用调整
   */
  disabled?: boolean
}

export default function ReviewLayout({
  leftPanel,
  rightPanel,
  initialLeftPercent = 40,
  minLeftPercent = 20,
  maxLeftPercent = 60,
  separatorWidth = 8,
  disabled = false,
}: ReviewLayoutProps) {
  const [leftPercent, setLeftPercent] = useState(initialLeftPercent)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // 处理拖拽开始（鼠标）
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    if (disabled) return
    e.preventDefault()
    setIsDragging(true)
  }, [disabled])

  // 处理拖拽开始（触摸）
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (disabled) return
    e.preventDefault()
    setIsDragging(true)
  }, [disabled])

  // 处理拖拽移动
  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const containerWidth = containerRect.width
      const newLeftPercent = (e.clientX - containerRect.left) / containerWidth * 100

      // 限制在最小和最大百分比之间
      const clampedPercent = Math.max(
        minLeftPercent,
        Math.min(maxLeftPercent, newLeftPercent)
      )

      setLeftPercent(clampedPercent)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, minLeftPercent, maxLeftPercent])

  // 处理触摸事件（移动端支持）
  useEffect(() => {
    if (!isDragging) return

    const handleTouchMove = (e: TouchEvent) => {
      if (!containerRef.current) return

      const touch = e.touches[0]
      const containerRect = containerRef.current.getBoundingClientRect()
      const containerWidth = containerRect.width
      const newLeftPercent = (touch.clientX - containerRect.left) / containerWidth * 100

      const clampedPercent = Math.max(
        minLeftPercent,
        Math.min(maxLeftPercent, newLeftPercent)
      )

      setLeftPercent(clampedPercent)
    }

    const handleTouchEnd = () => {
      setIsDragging(false)
    }

    document.addEventListener('touchmove', handleTouchMove, { passive: false })
    document.addEventListener('touchend', handleTouchEnd)

    return () => {
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', handleTouchEnd)
    }
  }, [isDragging, minLeftPercent, maxLeftPercent])

  // 右侧百分比
  const rightPercent = 100 - leftPercent

  return (
    <div
      ref={containerRef}
      className="flex h-full w-full overflow-hidden"
      style={{ cursor: isDragging ? 'col-resize' : 'default' }}
    >
      {/* 左侧面板 - 审核结果 */}
      <div
        className="flex-shrink-0 overflow-auto bg-white border-r border-gray-200"
        style={{ width: `${leftPercent}%` }}
      >
        {leftPanel}
      </div>

      {/* 分隔条 */}
      <div
        className={`
          flex-shrink-0 relative z-10 transition-colors
          ${isDragging ? 'bg-blue-500' : 'bg-gray-200 hover:bg-gray-300'}
          ${disabled ? 'cursor-default' : 'cursor-col-resize'}
        `}
        style={{ width: `${separatorWidth}px` }}
        onMouseDown={handleDragStart}
        onTouchStart={handleTouchStart}
      >
        {/* 分隔条中心线 */}
        <div
          className={`
            absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2
            w-1 h-8 rounded-full
            ${isDragging ? 'bg-white' : 'bg-gray-400'}
          `}
        />
      </div>

      {/* 右侧面板 - 文档预览 */}
      <div
        className="flex-shrink-0 overflow-auto bg-gray-50"
        style={{ width: `${rightPercent}%` }}
      >
        {rightPanel}
      </div>
    </div>
  )
}

/**
 * 用于在页面中嵌入 ReviewLayout 的容器组件
 */
interface ReviewLayoutContainerProps {
  leftPanel: ReactNode
  rightPanel: ReactNode
  header?: ReactNode
}

export function ReviewLayoutContainer({
  leftPanel,
  rightPanel,
  header,
}: ReviewLayoutContainerProps) {
  return (
    <div className="flex flex-col h-screen">
      {/* 头部（可选） */}
      {header && (
        <div className="flex-shrink-0 bg-white border-b border-gray-200">
          {header}
        </div>
      )}

      {/* 主内容区域 */}
      <div className="flex-1 overflow-hidden">
        <ReviewLayout
          leftPanel={leftPanel}
          rightPanel={rightPanel}
          initialLeftPercent={40}
          minLeftPercent={20}
          maxLeftPercent={60}
        />
      </div>
    </div>
  )
}
