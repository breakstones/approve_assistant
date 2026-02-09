import { Routes, Route, Navigate } from 'react-router-dom'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import ReviewPage from './pages/ReviewPage'

// Placeholder pages - to be implemented in subsequent tasks

function RulesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">规则管理</h1>
      <p className="text-gray-600">规则管理页面正在开发中...</p>
    </div>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">TrustLens AI</h1>
            <nav className="flex space-x-4">
              <a href="/" className="text-gray-600 hover:text-gray-900">首页</a>
              <a href="/upload" className="text-gray-600 hover:text-gray-900">上传文档</a>
              <a href="/review" className="text-gray-600 hover:text-gray-900">审核结果</a>
              <a href="/rules" className="text-gray-600 hover:text-gray-900">规则管理</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/review/:reviewId?" element={<ReviewPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
