import React, { useState, useRef, useEffect } from 'react'
import { getAIResponse, getSubmissions, type Submission } from '../services/api'
import type { Exercise } from '../types'

interface Message {
  who: 'user' | 'ai'
  text: string
  sql_query?: string
  query_result?: { columns: string[]; rows: any[][]; row_count: number }
  executed?: boolean
  intent?: string
}

interface Props {
  exercise: Exercise | null
  userQuery?: string
  error?: string
  demoMode: boolean
  onClose?: () => void // 新增关闭回调
}

export default function AIChat({ exercise, userQuery, error, demoMode, onClose }: Props) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // 当exercise改变时，获取该problem的submissions
  useEffect(() => {
    if (exercise && !demoMode) {
      getSubmissions(exercise.id, demoMode)
        .then(data => {
          setSubmissions(data)
          console.log(`[AIChat] Loaded ${data.length} submissions for exercise ${exercise.id}`)
        })
        .catch(err => {
          console.error('[AIChat] Failed to load submissions:', err)
          setSubmissions([])
        })
    } else {
      setSubmissions([])
    }
  }, [exercise?.id, demoMode])

  const send = async () => {
    if (!exercise || !input.trim()) return
    setMessages((prev) => [...prev, { who: 'user', text: input }])
    const msg = input
    setInput('')
    setLoading(true)
    try {
      const res = await getAIResponse(exercise.id, msg, userQuery, error, demoMode, submissions)
      setMessages((prev) => [
        ...prev,
        {
          who: 'ai',
          text: res.response,
          sql_query: res.sql_query,
          query_result: res.query_result,
          executed: res.executed,
          intent: res.intent,
        },
      ])
    } catch (e) {
      setMessages((prev) => [...prev, { who: 'ai', text: 'Error contacting AI' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }

  const renderQueryResult = (result: Message['query_result']) => {
      if (!result || result.row_count === 0) return null
      return (
        <div className="mt-2 overflow-x-auto border border-gray-100 rounded-xl bg-gray-50/50 shadow-sm">
          <table className="w-full text-[10px]">
            <thead className="bg-gray-100/50">
              <tr>{result.columns.map((c, i) => <th key={i} className="px-3 py-1.5 text-left font-bold text-gray-500">{c}</th>)}</tr>
            </thead>
            <tbody>
              {result.rows.slice(0, 3).map((r, i) => <tr key={i} className="border-t border-gray-100">{r.map((c, j) => <td key={j} className="px-3 py-1.5 text-gray-700">{String(c)}</td>)}</tr>)}
            </tbody>
          </table>
        </div>
      )
  }

  const renderMessage = (m: Message, i: number) => {
    const isUser = m.who === 'user'
    return (
      <div key={i} className={`flex w-full mb-5 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {!isUser && (
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 mr-2 flex items-center justify-center text-white text-[10px] shadow-sm shrink-0 mt-1">AI</div>
        )}
        <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
          {/* 气泡样式调整：AI气泡变为白色背景，适应灰色侧边栏 */}
          <div className={`px-4 py-2.5 rounded-2xl text-sm shadow-sm ${
            isUser 
              ? 'bg-blue-600 text-white rounded-br-sm' 
              : 'bg-white border border-gray-100 text-gray-900 rounded-bl-sm'
            }`}
          >
            <p className="whitespace-pre-wrap">{m.text}</p>
          </div>
          {!isUser && (m.sql_query || m.query_result) && (
             <div className="mt-2 pl-1 w-full animate-fade-in-up">
               {m.sql_query && <div className="bg-[#1e1e1e] text-blue-200 p-3 rounded-xl text-[10px] font-mono overflow-x-auto shadow-md border border-gray-700/50">{m.sql_query}</div>}
               {m.executed && m.query_result && renderQueryResult(m.query_result)}
             </div>
          )}
        </div>
      </div>
    )
  }

  return (
    // 背景改为灰色 #FAFAFA
    <div className="h-full flex flex-col bg-[#FAFAFA]">
      
      {/* Header: 高度 h-14，与 Layout 对齐 */}
      <div className="h-14 shrink-0 flex items-center justify-between px-5 border-b border-gray-200/50">
        <div className="flex items-center gap-2">
           <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
           <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wide">AI Assistant</h3>
        </div>
        
        <div className="flex items-center gap-1">
          {/* Clear Button */}
          <button onClick={() => setMessages([])} className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors" title="Clear Chat">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
          </button>
          
          {/* Close Sidebar Button (Only shows if onClose provided) */}
          {onClose && (
             <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors" title="Close AI Sidebar">
               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
             </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
            <div className="w-12 h-12 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-3">
              <span className="text-2xl grayscale">✨</span>
            </div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wide">How can I help?</p>
          </div>
        ) : (
          messages.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area: 背景适配灰色 */}
      <div className="p-4 border-t border-gray-200/50 bg-[#FAFAFA]">
        <div className="relative">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full pl-5 pr-12 py-3 rounded-full bg-white border border-gray-200 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all shadow-sm"
            placeholder="Ask AI..."
            disabled={loading || !exercise}
          />
          <button
             onClick={send}
             disabled={loading || !exercise || !input.trim()}
             className="absolute right-1.5 top-1.5 w-9 h-9 flex items-center justify-center bg-blue-600 text-white rounded-full disabled:opacity-50 hover:bg-blue-700 hover:scale-105 active:scale-95 transition-all shadow-md shadow-blue-500/20"
          >
             <svg className="w-4 h-4 translate-x-px" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
          </button>
        </div>
      </div>
    </div>
  )
}