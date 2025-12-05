import React, { useState, useEffect } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useNavigate, useLocation } from 'react-router-dom'

export default function AuthPage() {
  const { isAuthenticated, setAuth } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // 使用相对路径，通过Vite proxy转发，避免跨域问题
  const API_BASE = '/api/auth'

  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      // 不要在这里跳转，让 handleSubmit 里的逻辑处理
      // 注释掉或删除这段
    }
  }, [isAuthenticated, navigate, location])

const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setIsLoading(true)

    const url = mode === 'login' ? `${API_BASE}/login/` : `${API_BASE}/signup/`

    try {
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username, 
          password,
          ...(mode === 'signup' && email ? { email } : {})
        }),
      })

      // 先读取响应文本（响应流只能读取一次）
      const responseText = await res.text()
      
      let data
      try {
        // 尝试解析 JSON
        data = JSON.parse(responseText)
      } catch (jsonError) {
        // 如果响应不是 JSON 格式
        console.error('Non-JSON response:', responseText)
        setErrorMsg(`Server error: ${res.status} ${res.statusText}`)
        return
      }

      if (!res.ok) {
        setErrorMsg(data.error || data.message || `Request failed: ${res.status}`)
      } else {
        // 1. 获取角色 (默认 fallback 为 student)
        const userRole = data.role || 'student' 

        // 2. 更新 Context 状态
        setAuth({
          isAuthenticated: true,
          username: data.username || username,
          role: userRole, // 🟢 关键：把角色存入 Context
        })

        // 3. 🟢 关键：根据角色分流跳转
        if (userRole === 'instructor') {
          console.log('Redirecting to Instructor Dashboard...')
          navigate('/instructor')
        } else {
          console.log('Redirecting to Student Workspace...')
          navigate('/')
        }
      }
    } catch (err) {
      console.error('Signup/Login error:', err)
      // 尝试获取更详细的错误信息
      if (err instanceof Error) {
        setErrorMsg(err.message || 'Network error. Please try again.')
      } else {
        setErrorMsg('Network error. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#F5F5F7] p-4 font-sans text-gray-900">
      {/* 极简背景 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
         <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-blue-200/20 rounded-full blur-[100px]" />
         <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-purple-200/20 rounded-full blur-[100px]" />
      </div>

      {/* 卡片：超大圆角 rounded-3xl */}
      <div className="w-full max-w-[380px] bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/50 p-10 flex flex-col items-center relative z-10 animate-fade-in-up">
        
        {/* Back Button: Circle */}
        <button
          onClick={() => navigate('/')}
          className="absolute top-5 left-5 w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-all"
          title="Back to Home"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>

        <h1 className="text-2xl font-bold tracking-tight mb-3 mt-4">
          {mode === 'login' ? 'Welcome' : 'Join Us'}
        </h1>
        <p className="text-sm text-gray-500 mb-8 text-center">
          {mode === 'login' ? 'Sign in to access your workspace.' : 'Create an account to get started.'}
        </p>

        {/* Switcher: 全圆角胶囊 */}
        <div className="w-full bg-gray-100 p-1.5 rounded-full flex items-center mb-8">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-full transition-all duration-200 ${
              mode === 'login' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode('signup')}
            className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-full transition-all duration-200 ${
              mode === 'signup' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="w-full space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-500 ml-3 uppercase tracking-wide">Username</label>
            {/* Input: 全圆角胶囊 rounded-full */}
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-6 py-3.5 bg-gray-50 border border-gray-200 rounded-full text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all shadow-sm"
              placeholder="username"
              required
            />
          </div>

          {mode === 'signup' && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 ml-3 uppercase tracking-wide">Email (Optional)</label>
              {/* Input: 全圆角胶囊 rounded-full */}
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-6 py-3.5 bg-gray-50 border border-gray-200 rounded-full text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all shadow-sm"
                placeholder="email@example.com"
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-500 ml-3 uppercase tracking-wide">Password</label>
            {/* Input: 全圆角胶囊 rounded-full */}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-6 py-3.5 bg-gray-50 border border-gray-200 rounded-full text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all shadow-sm"
              placeholder="••••••••"
              required
            />
          </div>

          {errorMsg && (
            <div className="text-xs font-medium text-red-500 bg-red-50 px-4 py-2 rounded-full border border-red-100 flex items-center justify-center">
              {errorMsg}
            </div>
          )}

          {/* Button: 全圆角胶囊 rounded-full + 阴影 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-4 bg-gray-900 hover:bg-black text-white font-bold rounded-full shadow-lg shadow-gray-900/20 transition-all transform active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed mt-4"
          >
            {isLoading ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}