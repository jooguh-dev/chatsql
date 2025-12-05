import React, { useState, useEffect, useMemo } from 'react'
import { getExercises } from '../services/api'
import type { Exercise as Ex } from '../types'

interface Props {
  selectedId: number | null
  onSelect: (id: number) => void
  demoMode: boolean
}

export default function ProblemList({ selectedId, onSelect, demoMode }: Props) {
  const [exercises, setExercises] = useState<Ex[]>([])
  const [allExercises, setAllExercises] = useState<Ex[]>([]) // 存储所有exercises用于提取tags
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('')
  const [selectedTag, setSelectedTag] = useState<string>('')

  // 获取所有唯一的tags（从所有exercises中提取，不受filter影响）
  const allTags = useMemo(() => {
    const tagSet = new Set<string>()
    allExercises.forEach(ex => {
      if (ex.tags && Array.isArray(ex.tags)) {
        ex.tags.forEach(tag => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  }, [allExercises])

  // 首次加载：获取所有exercises（用于提取tags）
  useEffect(() => {
    loadAllExercises()
  }, [demoMode])

  // 当filter改变时：使用dynamic SQL筛选
  useEffect(() => {
    if (allExercises.length > 0) {
      loadFilteredExercises()
    }
  }, [selectedDifficulty, selectedTag, demoMode])

  async function loadAllExercises() {
    try {
      setIsLoading(true)
      const ex = await getExercises(demoMode, {})
      setAllExercises(ex)
      setExercises(ex) // 初始显示所有
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  async function loadFilteredExercises() {
    try {
      setIsLoading(true)
      const params: any = {}
      if (selectedDifficulty) {
        params.difficulty = selectedDifficulty
      }
      if (selectedTag) {
        params.tag = selectedTag
      }
      // 如果有filter，使用dynamic SQL从服务器获取筛选结果
      if (selectedDifficulty || selectedTag) {
        const ex = await getExercises(demoMode, params)
        setExercises(ex)
      } else {
        // 没有filter，显示所有
        setExercises(allExercises)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  // 辅助函数：难度颜色
  const getDifficultyColor = (diff?: string) => {
    switch (diff?.toLowerCase()) {
      case 'easy': return 'bg-green-100 text-green-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'hard': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3 px-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-gray-200 rounded-xl animate-pulse"></div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Filter Section */}
      <div className="px-2 space-y-2">
        {/* Difficulty Filter */}
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5 block">
            Difficulty
          </label>
          <div className="flex gap-1.5">
            {['', 'easy', 'medium', 'hard'].map((diff) => (
              <button
                key={diff || 'all'}
                onClick={() => setSelectedDifficulty(diff)}
                className={`
                  px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all active:scale-95
                  ${selectedDifficulty === diff
                    ? diff === 'easy' ? 'bg-green-500 text-white' :
                      diff === 'medium' ? 'bg-yellow-500 text-white' :
                      diff === 'hard' ? 'bg-red-500 text-white' :
                      'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {diff || 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* Tag Filter */}
        {allTags.length > 0 && (
          <div>
            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5 block">
              Tags
            </label>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => setSelectedTag('')}
                className={`
                  px-2.5 py-1 rounded-full text-[10px] font-bold transition-all active:scale-95
                  ${selectedTag === ''
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                All
              </button>
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(selectedTag === tag ? '' : tag)}
                  className={`
                    px-2.5 py-1 rounded-full text-[10px] font-bold transition-all active:scale-95
                    ${selectedTag === tag
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }
                  `}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Active Filters Indicator */}
        {(selectedDifficulty || selectedTag) && (
          <div className="flex items-center gap-2 text-[10px] text-gray-500">
            <span>Active filters:</span>
            {selectedDifficulty && (
              <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-700 font-semibold">
                {selectedDifficulty}
              </span>
            )}
            {selectedTag && (
              <span className="px-2 py-0.5 bg-blue-100 rounded text-blue-700 font-semibold">
                {selectedTag}
              </span>
            )}
            <button
              onClick={() => {
                setSelectedDifficulty('')
                setSelectedTag('')
              }}
              className="text-blue-600 hover:text-blue-700 font-semibold transition-all active:scale-95"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Problem List */}
      <div className="space-y-1">
        {exercises.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-400 text-sm">
            No problems found
          </div>
        ) : (
          exercises.map((ex, index) => {
        const isSelected = selectedId === ex.id
        return (
          <div
            key={ex.id}
            onClick={() => onSelect(ex.id)}
            className={`
              group relative flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all duration-200 border active:scale-[0.98]
              ${isSelected 
                ? 'bg-white border-blue-200 shadow-sm ring-1 ring-blue-100' 
                : 'bg-white border-transparent hover:bg-white hover:shadow-sm hover:border-gray-200'
              }
            `}
          >
            <div className="flex items-center gap-4">
              {/* Index Number Circle */}
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors
                ${isSelected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'}
              `}>
                {index + 1}
              </div>

              {/* Title & Schema */}
              <div>
                <h3 className={`text-sm font-semibold ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                  {ex.title}
                </h3>
                <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                  <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                  {ex.schema.display_name}
                </p>
              </div>
            </div>

            {/* Right Side: Badge & Arrow */}
            <div className="flex items-center gap-4">
              <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${getDifficultyColor(ex.difficulty)}`}>
                {ex.difficulty}
              </span>
              
              {/* Chevron Icon (iOS style) */}
              <svg 
                className={`w-5 h-5 transition-transform ${isSelected ? 'text-blue-500 translate-x-1' : 'text-gray-300 group-hover:text-gray-400'}`} 
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        )
      })}
      </div>
    </div>
  )
}