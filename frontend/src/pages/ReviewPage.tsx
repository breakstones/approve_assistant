/**
 * Review Page
 * 审核结果页面 - 使用双屏布局
 */
import { useParams } from 'react-router-dom'
import { ReviewLayoutContainer } from '../components'

export default function ReviewPage() {
  const { reviewId } = useParams()

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
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            审核结果列表
          </h2>
          <div className="text-sm text-gray-500">
            <p>审核结果组件正在开发中... (TASK-504)</p>
            <ul className="mt-2 space-y-1 text-xs">
              <li>• 规则列表展示</li>
              <li>• 状态标识（PASS/RISK/MISSING）</li>
              <li>• 点击展开详情</li>
              <li>• 风险等级视觉区分</li>
              <li>• 按类别/状态过滤</li>
            </ul>
          </div>
        </div>
      }
      rightPanel={
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            文档预览
          </h2>
          <div className="text-sm text-gray-500">
            <p>PDF 预览组件正在开发中... (TASK-505)</p>
            <ul className="mt-2 space-y-1 text-xs">
              <li>• PDF.js 集成</li>
              <li>• 渲染文档内容</li>
              <li>• 基于 bbox 的高亮显示</li>
              <li>• 页码导航</li>
              <li>• 缩放控制</li>
            </ul>
          </div>
        </div>
      }
    />
  )
}
