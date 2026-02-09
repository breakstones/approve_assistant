/**
 * PDF Viewer Component
 * PDF 文档预览组件
 *
 * 使用 PDF.js 渲染 PDF 文档，支持高亮显示
 */
import { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import * as pdfjsLib from 'pdfjs-dist'

// 设置 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

interface HighlightArea {
  page: number
  bbox: {
    x1: number
    y1: number
    x2: number
    y2: number
  }
  color?: string
  id?: string
}

interface PDFViewerProps {
  /**
   * PDF 文件 URL 或 Blob
   */
  fileUrl: string | Blob

  /**
   * 需要高亮显示的区域列表
   */
  highlights?: HighlightArea[]

  /**
   * 初始页码（1-based）
   */
  initialPage?: number

  /**
   * 初始缩放比例
   */
  initialScale?: number

  /**
   * 高亮区域点击回调
   */
  onHighlightClick?: (highlight: HighlightArea) => void

  /**
   * 页面变化回调
   */
  onPageChange?: (pageNumber: number) => void

  /**
   * 加载状态回调
   */
  onLoad?: (numPages: number) => void

  /**
   * 错误回调
   */
  onError?: (error: Error) => void
}

// 缩放级别选项
const SCALE_OPTIONS = [0.5, 0.75, 1, 1.25, 1.5, 2]

export default function PDFViewer({
  fileUrl,
  highlights = [],
  initialPage = 1,
  initialScale = 1,
  onHighlightClick,
  onPageChange,
  onLoad,
  onError,
}: PDFViewerProps) {
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null)
  const [numPages, setNumPages] = useState(0)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [scale, setScale] = useState(initialScale)
  const [rendering, setRendering] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const highlightLayerRef = useRef<HTMLDivElement>(null)

  // 加载 PDF 文档
  useEffect(() => {
    let mounted = true

    const loadPdf = async () => {
      setLoading(true)
      setError(null)

      try {
        // Convert Blob to Uint8Array if needed
        let source: string | Uint8Array = fileUrl as string
        if (fileUrl instanceof Blob) {
          const arrayBuffer = await fileUrl.arrayBuffer()
          source = new Uint8Array(arrayBuffer)
        }

        const loadingTask = pdfjsLib.getDocument(source)
        const pdf = await loadingTask.promise

        if (!mounted) return

        setPdfDoc(pdf)
        setNumPages(pdf.numPages)
        setLoading(false)
        onLoad?.(pdf.numPages)
      } catch (err) {
        if (!mounted) return

        const error = err instanceof Error ? err : new Error('Failed to load PDF')
        setError(error)
        setLoading(false)
        onError?.(error)
      }
    }

    loadPdf()

    return () => {
      mounted = false
    }
  }, [fileUrl, onLoad, onError])

  // 渲染当前页面
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return

    const renderPage = async () => {
      setRendering(true)

      try {
        const page = await pdfDoc.getPage(currentPage)
        const viewport = page.getViewport({ scale })

        const canvas = canvasRef.current!
        const context = canvas.getContext('2d', { alpha: false })

        if (!context) throw new Error('Failed to get canvas context')

        // 设置 canvas 尺寸
        canvas.height = viewport.height
        canvas.width = viewport.width

        // 渲染 PDF 页面
        await page.render({
          canvasContext: context,
          viewport: viewport,
        }).promise

        // 渲染高亮层
        renderHighlights(viewport)

        setRendering(false)
      } catch (err) {
        console.error('Failed to render page:', err)
        setRendering(false)
      }
    }

    renderPage()
  }, [pdfDoc, currentPage, scale, highlights])

  // 渲染高亮层
  const renderHighlights = useCallback(
    (viewport: pdfjsLib.PageViewport) => {
      if (!highlightLayerRef.current || !containerRef.current) return

      const layer = highlightLayerRef.current
      layer.innerHTML = ''

      // 筛选当前页的高亮区域
      const currentPageHighlights = highlights.filter((h) => h.page === currentPage)

      if (currentPageHighlights.length === 0) return

      // 获取 canvas 引用（用于后续可能的扩展）
      const canvas = canvasRef.current
      if (!canvas) return

      currentPageHighlights.forEach((highlight) => {
        const div = document.createElement('div')
        div.className = 'absolute cursor-pointer transition-opacity hover:opacity-80'
        div.id = highlight.id || `highlight-${highlight.page}-${highlight.bbox.x1}`

        // 计算 bbox 在 canvas 上的位置
        const x = (highlight.bbox.x1 / 72) * viewport.width
        const y = viewport.height - (highlight.bbox.y2 / 72) * viewport.height
        const width = ((highlight.bbox.x2 - highlight.bbox.x1) / 72) * viewport.width
        const height = ((highlight.bbox.y2 - highlight.bbox.y1) / 72) * viewport.height

        div.style.left = `${x}px`
        div.style.top = `${y}px`
        div.style.width = `${width}px`
        div.style.height = `${height}px`
        div.style.backgroundColor = highlight.color || 'rgba(255, 200, 0, 0.3)'
        div.style.border = '2px solid ' + (highlight.color || 'rgba(255, 150, 0, 0.8)')

        div.onclick = () => onHighlightClick?.(highlight)

        layer.appendChild(div)
      })
    },
    [currentPage, highlights, onHighlightClick]
  )

  // 跳转到指定页
  const goToPage = useCallback(
    (pageNumber: number) => {
      if (!pdfDoc) return
      const page = Math.max(1, Math.min(pageNumber, numPages))
      setCurrentPage(page)
      onPageChange?.(page)
    },
    [pdfDoc, numPages, onPageChange]
  )

  // 上一页
  const previousPage = useCallback(() => {
    goToPage(currentPage - 1)
  }, [currentPage, goToPage])

  // 下一页
  const nextPage = useCallback(() => {
    goToPage(currentPage + 1)
  }, [currentPage, goToPage])

  // 放大
  const zoomIn = useCallback(() => {
    const currentIndex = SCALE_OPTIONS.indexOf(scale)
    if (currentIndex < SCALE_OPTIONS.length - 1) {
      setScale(SCALE_OPTIONS[currentIndex + 1])
    }
  }, [scale])

  // 缩小
  const zoomOut = useCallback(() => {
    const currentIndex = SCALE_OPTIONS.indexOf(scale)
    if (currentIndex > 0) {
      setScale(SCALE_OPTIONS[currentIndex - 1])
    }
  }, [scale])

  // 键盘导航
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        previousPage()
      } else if (e.key === 'ArrowRight') {
        nextPage()
      } else if (e.key === '+' || e.key === '=') {
        zoomIn()
      } else if (e.key === '-') {
        zoomOut()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [previousPage, nextPage, zoomIn, zoomOut])

  // 计算当前页的高亮数量
  const currentPageHighlightCount = useMemo(() => {
    return highlights.filter((h) => h.page === currentPage).length
  }, [highlights, currentPage])

  // 加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  // 错误状态
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-red-600">
          <svg
            className="mx-auto h-12 w-12 mb-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p className="font-medium">加载失败</p>
          <p className="text-sm text-gray-500 mt-1">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* 工具栏 */}
      <div className="flex-shrink-0 flex items-center justify-between p-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          {/* 缩放控制 */}
          <button
            onClick={zoomOut}
            disabled={scale === SCALE_OPTIONS[0]}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="缩小"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <span className="text-sm text-gray-700 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={zoomIn}
            disabled={scale === SCALE_OPTIONS[SCALE_OPTIONS.length - 1]}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="放大"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {/* 页面导航 */}
          <button
            onClick={previousPage}
            disabled={currentPage <= 1}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="上一页"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-sm text-gray-700 min-w-[80px] text-center">
            {currentPage} / {numPages}
          </span>
          <button
            onClick={nextPage}
            disabled={currentPage >= numPages}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="下一页"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* 高亮提示 */}
        {currentPageHighlightCount > 0 && (
          <div className="flex items-center gap-1 text-xs text-orange-600">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span>{currentPageHighlightCount} 个高亮</span>
          </div>
        )}
      </div>

      {/* PDF 渲染区域 */}
      <div className="flex-1 overflow-auto p-4" ref={containerRef}>
        {rendering && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        <div className="relative inline-block mx-auto shadow-lg">
          <canvas ref={canvasRef} className="block" />
          <div ref={highlightLayerRef} className="absolute top-0 left-0 w-full h-full pointer-events-none" />
        </div>
      </div>
    </div>
  )
}
