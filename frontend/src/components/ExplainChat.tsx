/**
 * Explain Chat Component
 * 追问交互 UI 组件
 *
 * 多轮追问聊天界面，关联审核结果上下文
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { explainApi, type ExplainResponse, type ConversationMessage } from '../api'

export interface ExplainChatProps {
  /**
   * 审查任务 ID
   */
  reviewId: string

  /**
   * 审核结果 ID
   */
  resultId: string

  /**
   * 规则信息
   */
  ruleInfo?: {
    rule_id: string
    name: string
    intent: string
  }

  /**
   * 会话 ID（用于恢复历史对话）
   */
  sessionId?: string

  /**
   * 会话创建/更新回调
   */
  onSessionChange?: (sessionId: string) => void

  /**
   * 最大显示消息数量
   */
  maxMessages?: number
}

// 消息类型
type ChatMessage = ConversationMessage & {
  // 扩展：用于解析 JSON 格式的助手回复
  parsedData?: ExplainResponse
}

export default function ExplainChat({
  reviewId,
  resultId,
  ruleInfo,
  sessionId: initialSessionId,
  onSessionChange,
  maxMessages = 50,
}: ExplainChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)
  const [error, setError] = useState<string | null>(null)

  const inputRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 加载对话历史
  useEffect(() => {
    if (sessionId) {
      loadHistory()
    }
  }, [sessionId])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 加载对话历史
  const loadHistory = async () => {
    if (!sessionId) return

    try {
      const history = await explainApi.getHistory(sessionId)

      // 解析助手的 JSON 回复
      const parsedMessages: ChatMessage[] = history.messages.map(msg => {
        if (msg.role === 'assistant') {
          try {
            const parsed = JSON.parse(msg.content)
            return { ...msg, parsedData: parsed }
          } catch {
            return msg
          }
        }
        return msg
      })

      setMessages(parsedMessages)
    } catch (err) {
      console.error('Failed to load conversation history:', err)
    }
  }

  // 发送消息
  const sendMessage = useCallback(async () => {
    const trimmedInput = input.trim()
    if (!trimmedInput || loading) return

    // 添加用户消息
    const userMessage: ChatMessage = {
      message_id: `msg_${Date.now()}_user`,
      role: 'user',
      content: trimmedInput,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setError(null)
    setLoading(true)

    // 聚焦回输入框
    setTimeout(() => {
      inputRef.current?.focus()
    }, 100)

    try {
      // 调用解释 API
      const response = await explainApi.ask({
        review_id: reviewId,
        result_id: resultId,
        question: trimmedInput,
        session_id: sessionId,
      })

      // 更新会话 ID
      if (response.session_id !== sessionId) {
        setSessionId(response.session_id)
        onSessionChange?.(response.session_id)
      }

      // 添加助手消息（将响应转为 JSON 字符串存储）
      const assistantMessage: ChatMessage = {
        message_id: response.message_id,
        role: 'assistant',
        content: JSON.stringify(response),
        timestamp: response.timestamp,
        parsedData: response,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '发送失败'
      setError(errorMessage)

      // 移除用户消息（发送失败）
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }, [input, loading, reviewId, resultId, sessionId, onSessionChange])

  // 处理键盘事件（Enter 发送，Shift+Enter 换行）
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // 快速问题建议
  const quickQuestions = [
    '为什么判定为' + (ruleInfo ? ruleInfo.name : '这个结果') + '？',
    '具体在原文的哪里？',
    '应该如何修改？',
  ]

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 头部：规则信息 */}
      {ruleInfo && (
        <div className="flex-shrink-0 p-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">{ruleInfo.name}</h3>
              <p className="text-xs text-gray-600 mt-1">{ruleInfo.intent}</p>
            </div>
            {sessionId && (
              <span className="text-xs text-gray-500">
                会话: {sessionId.slice(0, 8)}...
              </span>
            )}
          </div>
        </div>
      )}

      {/* 消息列表 */}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg
              className="w-12 h-12 mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <p className="text-sm">开始追问，了解更多审核细节</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.slice(-maxMessages).map((msg) => (
              <MessageBubble key={msg.message_id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 快速问题 */}
      {messages.length === 0 && (
        <div className="flex-shrink-0 p-3 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">快速提问：</p>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setInput(question)}
                className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入框 */}
      <div className="flex-shrink-0 p-3 border-t border-gray-200">
        {/* 错误提示 */}
        {error && (
          <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
            {error}
          </div>
        )}

        {/* 输入区域 */}
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题... (Enter 发送，Shift+Enter 换行)"
            rows={1}
            disabled={loading}
            className={`
              flex-1 px-3 py-2 border rounded-lg resize-none
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${loading ? 'bg-gray-100 cursor-not-allowed' : ''}
            `}
            style={{
              minHeight: '40px',
              maxHeight: '120px',
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className={`
              px-4 py-2 rounded-lg transition-colors
              ${input.trim() && !loading
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {loading ? (
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </button>
        </div>

        {/* 提示文本 */}
        <p className="text-xs text-gray-500 mt-2">
          按 Enter 发送，Shift + Enter 换行
        </p>
      </div>
    </div>
  )
}

// 消息气泡组件
function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-br-sm">
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          <p className="text-xs text-blue-200 mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
    )
  }

  // 助手消息
  const parsedData = message.parsedData

  return (
    <div className="flex justify-start">
      <div className="max-w-[75%] bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm">
        {/* 解析后的结构化回答 */}
        {parsedData ? (
          <>
            <div className="mb-2">
              <p className="text-sm text-gray-800">{parsedData.answer}</p>
            </div>

            {/* 推理过程 */}
            {parsedData.reasoning && (
              <div className="mb-2 p-2 bg-blue-50 rounded">
                <p className="text-xs text-gray-600">
                  <span className="font-medium">推理：</span>
                  {parsedData.reasoning}
                </p>
              </div>
            )}

            {/* 证据引用 */}
            {parsedData.evidence_references && parsedData.evidence_references.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium text-gray-700 mb-1">引用证据：</p>
                <div className="space-y-1">
                  {parsedData.evidence_references.map((ref, idx) => (
                    <div key={idx} className="p-2 bg-white rounded border border-gray-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-700">
                          第 {ref.page} 页
                        </span>
                        <span className="text-xs text-gray-500">
                          {ref.relevance}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">
                        "{ref.quote}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 置信度 */}
            {parsedData.confidence && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-600">置信度：</span>
                <span className={`
                  px-2 py-0.5 text-xs font-medium rounded
                  ${parsedData.confidence === 'high' ? 'bg-green-100 text-green-700' : ''}
                  ${parsedData.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' : ''}
                  ${parsedData.confidence === 'low' ? 'bg-red-100 text-red-700' : ''}
                `}>
                  {parsedData.confidence === 'high' ? '高' : parsedData.confidence === 'medium' ? '中' : '低'}
                </span>
              </div>
            )}

            {/* 限制说明 */}
            {parsedData.limitations && parsedData.limitations.length > 0 && (
              <div className="mt-2 p-2 bg-yellow-50 rounded">
                <p className="text-xs text-yellow-800">
                  <span className="font-medium">注意：</span>
                  {parsedData.limitations.join('；')}
                </p>
              </div>
            )}
          </>
        ) : (
          // 未解析的原始文本
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{message.content}</p>
        )}

        <p className="text-xs text-gray-500 mt-2">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}
