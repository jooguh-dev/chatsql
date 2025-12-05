import React, { useState } from 'react'
import { createExercise } from '../services/api'

interface Props {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void // 创建成功后刷新列表
}

export default function CreateExerciseModal({ isOpen, onClose, onSuccess }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // 表单状态
  const [formData, setFormData] = useState({
    title: '',
    difficulty: 'Easy',
    description: '',
    initial_query: 'SELECT * FROM ',
    answer_query: '',
    schema_id: 1 // 默认 Schema ID，后续可改为下拉选择
  })

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await createExercise(formData)
      onSuccess() // 刷新父组件列表
      onClose()   // 关闭弹窗
      // 重置表单
      setFormData({ title: '', difficulty: 'Easy', description: '', initial_query: '', answer_query: '', schema_id: 1 })
    } catch (err: any) {
      setError(err.message || 'Failed to create exercise')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-gray-900/20 backdrop-blur-sm" onClick={onClose} />

      {/* Modal Window */}
      <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-gray-100 flex flex-col max-h-[90vh] animate-fade-in-up overflow-hidden">
        
        {/* Header */}
        <div className="px-8 py-5 border-b border-gray-100 flex items-center justify-between bg-white z-10">
          <div>
            <h2 className="text-lg font-bold text-gray-900">New Exercise</h2>
            <p className="text-xs text-gray-500">Create a new SQL challenge for students.</p>
          </div>
          <button onClick={onClose} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-all active:scale-95">
            <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Scrollable Form Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <form id="create-form" onSubmit={handleSubmit} className="space-y-6">
            
            {/* Title & Difficulty Row */}
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2 space-y-1.5">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wide">Title</label>
                <input 
                  required
                  className="w-full px-4 py-2.5 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none"
                  placeholder="e.g. Find all managers"
                  value={formData.title}
                  onChange={e => setFormData({...formData, title: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wide">Difficulty</label>
                <select 
                  className="w-full px-4 py-2.5 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white outline-none appearance-none cursor-pointer"
                  value={formData.difficulty}
                  onChange={e => setFormData({...formData, difficulty: e.target.value})}
                >
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>
            </div>

            {/* Description */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wide">Description (Markdown)</label>
              <textarea 
                required
                rows={4}
                className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none resize-none"
                placeholder="Describe the problem..."
                value={formData.description}
                onChange={e => setFormData({...formData, description: e.target.value})}
              />
            </div>

            {/* SQL Editors Row */}
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wide">Initial SQL</label>
                <textarea 
                  rows={5}
                  className="w-full px-4 py-3 rounded-xl bg-gray-900 text-blue-300 font-mono text-xs border border-gray-800 focus:ring-2 focus:ring-blue-500/50 outline-none resize-none"
                  value={formData.initial_query}
                  onChange={e => setFormData({...formData, initial_query: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-green-600 uppercase tracking-wide">Answer SQL (Solution)</label>
                <textarea 
                  rows={5}
                  className="w-full px-4 py-3 rounded-xl bg-gray-900 text-green-300 font-mono text-xs border border-gray-800 focus:ring-2 focus:ring-green-500/50 outline-none resize-none"
                  placeholder="SELECT * FROM..."
                  value={formData.answer_query}
                  onChange={e => setFormData({...formData, answer_query: e.target.value})}
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-50 text-red-600 text-sm border border-red-100 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {error}
              </div>
            )}

          </form>
        </div>

        {/* Footer */}
        <div className="px-8 py-5 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl text-sm font-bold text-gray-500 hover:bg-gray-200 transition-all active:scale-95"
          >
            Cancel
          </button>
          <button 
            type="submit" 
            form="create-form"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-bold shadow-lg shadow-gray-900/20 hover:bg-black active:scale-95 transition-all disabled:opacity-70 flex items-center gap-2"
          >
            {loading ? 'Saving...' : 'Create Exercise'}
          </button>
        </div>

      </div>
    </div>
  )
}