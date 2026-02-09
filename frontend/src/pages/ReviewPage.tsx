/**
 * Review Page
 * 审核结果页面 - 使用双屏布局
 */
import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { ReviewLayoutContainer, RuleList, PDFViewer } from '../components'
import { type ReviewResult, type Rule, type HighlightArea } from '../api'

// Mock 数据 - 实际应从 API 获取
const mockResults: ReviewResult[] = [
  {
    rule_id: 'payment_cycle_max_30',
    rule_name: '付款周期限制',
    status: 'RISK',
    reason: '合同约定付款周期为60天，超过规则要求的30天限制',
    evidence: [
      {
        chunk_id: 'doc_001_p3_c1',
        quote: '甲方应在验收合格后60个工作日内支付款项',
        page: 3,
        bbox: { x1: 100, y1: 200, x2: 400, y2: 250 },
        confidence: 0.95,
      },
    ],
    confidence: 0.9,
    suggestion: '建议将付款周期调整为不超过30天',
  },
  {
    rule_id: 'confidentiality_required',
    rule_name: '保密条款要求',
    status: 'PASS',
    reason: '合同中包含了完整的保密条款，明确了保密义务和期限',
    evidence: [
      {
        chunk_id: 'doc_001_p5_c2',
        quote: '双方应对在合作过程中获悉的对方商业秘密承担保密义务',
        page: 5,
        bbox: { x1: 80, y1: 150, x2: 380, y2: 180 },
        confidence: 0.92,
      },
      {
        chunk_id: 'doc_001_p5_c3',
        quote: '保密期限为合同终止后3年',
        page: 5,
        bbox: { x1: 80, y1: 185, x2: 350, y2: 210 },
        confidence: 0.88,
      },
    ],
    confidence: 0.95,
  },
  {
    rule_id: 'intellectual_property',
    rule_name: '知识产权归属',
    status: 'MISSING',
    reason: '合同中未找到关于知识产权归属的明确条款',
    evidence: [],
    confidence: 0.7,
    suggestion: '建议补充知识产权归属条款，明确双方在合作过程中产生的知识产权的归属',
  },
]

const mockRules: Rule[] = [
  {
    rule_id: 'payment_cycle_max_30',
    name: '付款周期限制',
    category: 'Payment',
    intent: '付款周期不得超过30天',
    type: 'numeric_constraint',
    params: { max_days: 30 },
    risk_level: 'HIGH',
    retrieval_tags: ['payment'],
    enabled: true,
  },
  {
    rule_id: 'confidentiality_required',
    name: '保密条款要求',
    category: 'Confidentiality',
    intent: '合同必须包含保密条款',
    type: 'requirement',
    params: { obligation: '保密义务' },
    risk_level: 'MEDIUM',
    retrieval_tags: ['confidentiality'],
    enabled: true,
  },
  {
    rule_id: 'intellectual_property',
    name: '知识产权归属',
    category: 'IP',
    intent: '合同应明确知识产权归属',
    type: 'requirement',
    params: {},
    risk_level: 'MEDIUM',
    retrieval_tags: ['ip', 'intellectual_property'],
    enabled: true,
  },
]

// 示例 PDF URL（实际应从文档服务获取）
const SAMPLE_PDF_URL = 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkeypldi.pdf'

export default function ReviewPage() {
  const { reviewId } = useParams()
  const [highlights, setHighlights] = useState<HighlightArea[]>([])
  const [pdfUrl] = useState<string | Blob>(SAMPLE_PDF_URL)

  // 证据点击处理（跳转到对应页并高亮）
  const handleEvidenceClick = useCallback((evidence: ReviewResult['evidence'][0]) => {
    if (!evidence.bbox) {
      console.warn('Evidence has no bbox:', evidence)
      return
    }

    const highlight: HighlightArea = {
      page: evidence.page,
      bbox: evidence.bbox,
      id: evidence.chunk_id,
    }

    setHighlights([highlight])

    // 平滑滚动到 PDF viewer
    // PDFViewer 会自动跳转到对应页
  }, [])

  // 高亮区域点击处理
  const handleHighlightClick = useCallback((highlight: HighlightArea) => {
    console.log('Highlight clicked:', highlight)
  }, [])

  return (
    <ReviewLayoutContainer
      header={
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-900">
              审核结果
            </h1>
            {reviewId && (
              <span className="text-sm text-gray-500">
                ID: {reviewId}
              </span>
            )}
          </div>
        </div>
      }
      leftPanel={
        <RuleList
          results={mockResults}
          rules={mockRules}
          onEvidenceClick={handleEvidenceClick}
        />
      }
      rightPanel={
        <div className="h-full">
          <div className="mb-2 px-4 py-2 bg-white border-b border-gray-200">
            <p className="text-xs text-gray-500">
              示例 PDF（实际应从后端获取文档）
            </p>
          </div>
          <PDFViewer
            fileUrl={pdfUrl}
            highlights={highlights}
            initialPage={highlights[0]?.page || 1}
            onHighlightClick={handleHighlightClick}
            onPageChange={(page) => {
              console.log('Page changed:', page)
            }}
          />
        </div>
      }
    />
  )
}
