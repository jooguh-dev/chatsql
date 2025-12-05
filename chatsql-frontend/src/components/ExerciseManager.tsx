import React, { useState, useEffect } from 'react'
import { getInstructorExercises } from '../services/api'
import type { Exercise } from '../types'
import CreateExerciseModal from './CreateExerciseModal'

export default function ExerciseManager() {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // 加载题目列表
  const loadExercises = async () => {
    setIsLoading(true)
    try {
      // 传入 true (demoMode) 或者 false 取决于你想看真实数据还是 mock
      // 这里建议 false 走真实后端
      const data = await getInstructorExercises()
      setExercises(data)
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadExercises()
  }, [])

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
        <h2 className="text-xl font-bold text-gray-900">Exercise Bank</h2>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="px-5 py-2.5 bg-gray-900 hover:bg-black text-white text-xs font-bold uppercase tracking-wide rounded-full shadow-lg shadow-gray-900/10 transition-all active:scale-95 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          Create Exercise
        </button>
      </div>

      {/* Exercise List */}
      {isLoading ? (
        <div className="text-center py-10 text-gray-400">Loading exercises...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {exercises.map((ex) => (
            <div key={ex.id} className="group bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-all flex items-center justify-between cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-500 transition-colors">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{ex.title}</h3>
                  <p className="text-xs text-gray-500 mt-0.5 truncate max-w-md">
                    {ex.description ? (ex.description.length > 60 ? ex.description.substring(0, 60) + '...' : ex.description) : 'No description'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase border ${
                  ex.difficulty === 'Easy' ? 'bg-green-50 text-green-700 border-green-100' :
                  ex.difficulty === 'Medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-100' :
                  'bg-red-50 text-red-700 border-red-100'
                }`}>
                  {ex.difficulty}
                </span>
                <svg className="w-5 h-5 text-gray-300 group-hover:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </div>
            </div>
          ))}
          
          {exercises.length === 0 && (
             <div className="text-center py-12 bg-white rounded-3xl border border-dashed border-gray-200">
               <p className="text-gray-400">No exercises found. Create one!</p>
             </div>
          )}
        </div>
      )}

      {/* Modal */}
      <CreateExerciseModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={loadExercises} // 创建成功后重新加载列表
      />
    </div>
  )
}