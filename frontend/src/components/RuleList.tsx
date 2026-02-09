/**
 * Rule List Component
 * 审核结果列表组件
 *
 * 展示规则列表与审核状态，支持过滤和展开详情
 */
import { useState, useMemo } from 'react'
import { type ReviewResult, type Rule } from '../api'

interface RuleListProps {
  /**
   * 审核结果列表
   */
  results: ReviewResult[]

  /**
   * 规则详情映射（用于获取额外信息）
   */
  rules?: Rule[]

  /**
   * 默认展开状态
   */
  defaultExpanded?: boolean

  /**
   * 点击结果项时的回调
   */
  onResultClick?: (result: ReviewResult) => void

  /**
   * 点击证据时的回调
   */
  onEvidenceClick?: (evidence: ReviewResult['evidence'][0]) => void
}

// 状态配置
const STATUS_CONFIG = {
  PASS: {
    label: '通过',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    borderColor: 'border-green-200',
    dotColor: 'bg-green-500',
  },
  RISK: {
    label: '风险',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
    dotColor: 'bg-orange-500',
  },
  MISSING: {
    label: '缺失',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
    dotColor: 'bg-red-500',
  },
  FAILED: {
    label: '失败',
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-200',
    dotColor: 'bg-gray-500',
  },
} as const

// 风险等级配置
const RISK_LEVEL_CONFIG = {
  HIGH: { label: '高', color: 'text-red-600', bgColor: 'bg-red-100' },
  MEDIUM: { label: '中', color: 'text-orange-600', bgColor: 'bg-orange-100' },
  LOW: { label: '低', color: 'text-green-600', bgColor: 'bg-green-100' },
} as const

// 过滤器选项
type FilterType = 'all' | 'pass' | 'risk' | 'missing'
type CategoryFilter = 'all' | string

export default function RuleList({
  results,
  rules = [],
  defaultExpanded: _defaultExpanded = false,
  onResultClick: _onResultClick,
  onEvidenceClick,
}: RuleListProps) {
  const [filterType, setFilterType] = useState<FilterType>('all')
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  // 获取可用的类别列表
  const categories = useMemo(() => {
    const cats = new Set(rules.map((r) => r.category))
    return Array.from(cats).sort()
  }, [rules])

  // 过滤结果
  const filteredResults = useMemo(() => {
    return results.filter((result) => {
      // 状态过滤
      if (filterType !== 'all' && result.status.toLowerCase() !== filterType) {
        return false
      }

      // 类别过滤
      if (categoryFilter !== 'all') {
        const rule = rules.find((r) => r.rule_id === result.rule_id)
        if (rule?.category !== categoryFilter) {
          return false
        }
      }

      return true
    })
  }, [results, filterType, categoryFilter, rules])

  // 切换展开状态
  const toggleExpand = (ruleId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(ruleId)) {
        next.delete(ruleId)
      } else {
        next.add(ruleId)
      }
      return next
    })
  }

  // 全部展开/收起
  const toggleAll = () => {
    if (expandedIds.size === filteredResults.length) {
      setExpandedIds(new Set())
    } else {
      setExpandedIds(new Set(filteredResults.map((r) => r.rule_id)))
    }
  }

  // 获取规则信息
  const getRuleInfo = (ruleId: string) => {
    return rules.find((r) => r.rule_id === ruleId)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 过滤器 */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 bg-white">
        {/* 状态过滤 */}
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-700 mb-2">
            状态筛选
          </label>
          <div className="flex flex-wrap gap-2">
            <FilterButton
              active={filterType === 'all'}
              onClick={() => setFilterType('all')}
            >
              全部 ({results.length})
            </FilterButton>
            <FilterButton
              active={filterType === 'risk'}
              onClick={() => setFilterType('risk')}
              color="orange"
            >
              风险 ({results.filter((r) => r.status === 'RISK').length})
            </FilterButton>
            <FilterButton
              active={filterType === 'missing'}
              onClick={() => setFilterType('missing')}
              color="red"
            >
              缺失 ({results.filter((r) => r.status === 'MISSING').length})
            </FilterButton>
            <FilterButton
              active={filterType === 'pass'}
              onClick={() => setFilterType('pass')}
              color="green"
            >
              通过 ({results.filter((r) => r.status === 'PASS').length})
            </FilterButton>
          </div>
        </div>

        {/* 类别过滤 */}
        {categories.length > 0 && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-2">
              类别筛选
            </label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">全部类别</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* 展开按钮 */}
        <button
          onClick={toggleAll}
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          {expandedIds.size === filteredResults.length ? '收起全部' : '展开全部'}
        </button>
      </div>

      {/* 结果列表 */}
      <div className="flex-1 overflow-auto">
        {filteredResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg
              className="w-12 h-12 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-sm">暂无审核结果</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredResults.map((result) => {
              const config = STATUS_CONFIG[result.status as keyof typeof STATUS_CONFIG]
              const ruleInfo = getRuleInfo(result.rule_id)
              const isExpanded = expandedIds.has(result.rule_id)

              return (
                <div
                  key={result.rule_id}
                  className={`border-l-4 ${config.borderColor.replace('border-', 'border-l-').replace('200', '500')}`}
                >
                  {/* 结果项头部 */}
                  <div
                    className={`
                      p-4 cursor-pointer transition-colors
                      ${isExpanded ? config.bgColor : 'hover:bg-gray-50'}
                    `}
                    onClick={() => toggleExpand(result.rule_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {/* 状态指示器 */}
                          <span
                            className={`
                              flex-shrink-0 w-2 h-2 rounded-full
                              ${config.dotColor}
                            `}
                          />

                          {/* 规则名称 */}
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {result.rule_name}
                          </h3>

                          {/* 风险等级标签 */}
                          {ruleInfo && (
                            <span
                              className={`
                                flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded
                                ${RISK_LEVEL_CONFIG[ruleInfo.risk_level].color}
                                ${RISK_LEVEL_CONFIG[ruleInfo.risk_level].bgColor}
                              `}
                            >
                              {RISK_LEVEL_CONFIG[ruleInfo.risk_level].label}风险
                            </span>
                          )}

                          {/* 状态标签 */}
                          <span
                            className={`
                              flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded
                              ${config.bgColor}
                              ${config.textColor}
                            `}
                          >
                            {config.label}
                          </span>
                        </div>

                        {/* 原因描述 */}
                        <p className="text-xs text-gray-600 line-clamp-2">
                          {result.reason}
                        </p>

                        {/* 证据数量 */}
                        {result.evidence.length > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            {result.evidence.length} 条证据
                          </p>
                        )}
                      </div>

                      {/* 展开图标 */}
                      <svg
                        className={`
                          flex-shrink-0 w-5 h-5 text-gray-400 transition-transform
                          ${isExpanded ? 'rotate-90' : ''}
                        `}
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

                  {/* 展开详情 */}
                  {isExpanded && (
                    <div className={`p-4 ${config.bgColor} border-t border-gray-200`}>
                      {/* 详细原因 */}
                      <div className="mb-4">
                        <h4 className="text-xs font-medium text-gray-700 mb-1">
                          审核说明
                        </h4>
                        <p className="text-sm text-gray-600">{result.reason}</p>
                      </div>

                      {/* 建议 */}
                      {result.suggestion && (
                        <div className="mb-4">
                          <h4 className="text-xs font-medium text-gray-700 mb-1">
                            修改建议
                          </h4>
                          <p className="text-sm text-gray-600">{result.suggestion}</p>
                        </div>
                      )}

                      {/* 证据列表 */}
                      {result.evidence.length > 0 ? (
                        <div>
                          <h4 className="text-xs font-medium text-gray-700 mb-2">
                            相关证据
                          </h4>
                          <div className="space-y-2">
                            {result.evidence.map((evidence, idx) => (
                              <EvidenceItem
                                key={`${evidence.chunk_id}-${idx}`}
                                evidence={evidence}
                                onClick={() => onEvidenceClick?.(evidence)}
                              />
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-500 italic">
                          暂无相关证据
                        </div>
                      )}

                      {/* 置信度 */}
                      {result.confidence !== undefined && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-600">置信度</span>
                            <span className="font-medium text-gray-900">
                              {Math.round(result.confidence * 100)}%
                            </span>
                          </div>
                          <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-blue-600 h-1.5 rounded-full"
                              style={{ width: `${result.confidence * 100}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// 过滤器按钮组件
function FilterButton({
  children,
  active,
  onClick,
  color = 'blue',
}: {
  children: React.ReactNode
  active: boolean
  onClick: () => void
  color?: 'blue' | 'green' | 'orange' | 'red'
}) {
  const colorClasses = {
    blue: active
      ? 'bg-blue-600 text-white'
      : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300',
    green: active
      ? 'bg-green-600 text-white'
      : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300',
    orange: active
      ? 'bg-orange-600 text-white'
      : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300',
    red: active
      ? 'bg-red-600 text-white'
      : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300',
  }

  return (
    <button
      onClick={onClick}
      className={`
        px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors
        ${colorClasses[color]}
      `}
    >
      {children}
    </button>
  )
}

// 证据项组件
function EvidenceItem({
  evidence,
  onClick,
}: {
  evidence: ReviewResult['evidence'][0]
  onClick?: () => void
}) {
  return (
    <div
      className={`
        p-3 rounded-lg border border-gray-200 bg-white
        ${onClick ? 'cursor-pointer hover:border-blue-300 hover:shadow-sm' : ''}
        transition-all
      `}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-1">
        <span className="text-xs font-medium text-gray-700">
          第 {evidence.page} 页
        </span>
        {evidence.confidence !== undefined && (
          <span className="text-xs text-gray-500">
            {Math.round(evidence.confidence * 100)}%
          </span>
        )}
      </div>
      <p className="text-xs text-gray-600 line-clamp-3">
        {evidence.quote}
      </p>
      {onClick && (
        <div className="mt-2 text-xs text-blue-600 flex items-center">
          <span>定位到原文</span>
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
      )}
    </div>
  )
}
