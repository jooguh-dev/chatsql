import React, { useEffect, useState } from 'react'
import ProblemList from './ProblemList'

interface Props {
  isOpen: boolean
  onClose: () => void
  selectedId: number | null
  onSelect: (id: number) => void
  demoMode: boolean
}

export default function ProblemModal({ isOpen, onClose, selectedId, onSelect, demoMode }: Props) {
  const [isVisible, setIsVisible] = useState(false)

  // 处理淡入淡出动画
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true)
    } else {
      const timer = setTimeout(() => setIsVisible(false), 200)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  if (!isVisible && !isOpen) return null

  const handleSelect = (id: number) => {
    onSelect(id)
    onClose()
  }

  const handleRandom = () => {
    const randomId = Math.floor(Math.random() * 3) + 1
    handleSelect(randomId)
  }

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-200 ${
        isOpen ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Backdrop with Blur */}
      <div 
        className="absolute inset-0 bg-gray-900/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Window */}
      <div
        className={`relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh] transform transition-all duration-200 ${
          isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header - macOS Style */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-white/80 backdrop-blur-md z-10 sticky top-0">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Select a Problem</h2>
            <p className="text-xs text-gray-500 mt-0.5">Choose an exercise to practice SQL</p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Random Button */}
            <button
              onClick={handleRandom}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              I'm Feeling Lucky
            </button>

            {/* Close Button (Circle X) */}
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors"
              aria-label="Close"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 custom-scrollbar p-4">
          <ProblemList selectedId={selectedId} onSelect={handleSelect} demoMode={demoMode} />
        </div>
      </div>
    </div>
  )
}