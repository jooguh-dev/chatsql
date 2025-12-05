import React from 'react'
import Editor from '@monaco-editor/react'
import type { Exercise, QueryResult, SubmitResult } from '../types'
import { executeQuery, submitQuery } from '../services/api'

interface Props {
  value: string
  onChange: (v: string) => void
  exercise: Exercise | null
  onExecute: (r: QueryResult) => void
  onSubmit: (r: SubmitResult) => void
  isLoading: boolean
  demoMode: boolean
}

export default function CodeEditor({
  value,
  onChange,
  exercise,
  onExecute,
  onSubmit,
  isLoading,
  demoMode,
}: Props) {
  const handleRun = async () => {
    if (!exercise) return
    try {
      const res = await executeQuery(exercise.id, value, demoMode)
      onExecute(res)
    } catch (e) { console.error(e) }
  }

  const handleSubmit = async () => {
    if (!exercise) return
    try {
      const res = await submitQuery(exercise.id, value, demoMode)
      onSubmit(res)
    } catch (e) { console.error(e) }
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="h-14 shrink-0 flex items-center justify-between px-5 border-b border-gray-50 bg-white">
        
        <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wide">
           <svg className="w-4 h-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
           </svg>
           <span>Editor</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Run Button */}
          <button
            onClick={handleRun}
            disabled={isLoading || !exercise}
            title="Run Code"
            className="w-9 h-9 flex items-center justify-center rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900 shadow-sm transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {isLoading ? (
              <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            ) : (
              <svg className="w-4 h-4 translate-x-px" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
            )}
          </button>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isLoading || !exercise}
            title="Submit Solution"
            className="w-9 h-9 flex items-center justify-center rounded-full bg-blue-500 text-white hover:bg-blue-600 shadow-md shadow-blue-500/30 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
          </button>
        </div>
      </div>

      <div className="flex-1 relative">
        <Editor
          height="100%"
          defaultLanguage="sql"
          value={value}
          onChange={(v) => onChange(v || '')}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            // 🟢 关键修改：强制使用 SF Mono (Apple 官方代码字体)
            fontFamily: '"SF Mono", "Menlo", "Monaco", "Courier New", monospace',
            fontSize: 13,
            lineHeight: 24,
            padding: { top: 20, bottom: 20 },
            lineNumbers: 'on',
            lineNumbersMinChars: 2,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            overviewRulerBorder: false,
            hideCursorInOverviewRuler: true,
            renderLineHighlight: 'all', 
            scrollbar: {
              useShadows: false,
              verticalHasArrows: false,
              horizontalHasArrows: false,
              vertical: 'visible',
              horizontal: 'visible',
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
            }
          }}
        />
      </div>
    </div>
  )
}