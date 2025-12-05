import React from 'react'
import type { QueryResult, SubmitResult } from '../types'

interface Props {
  queryResult: QueryResult | null
  submitResult: SubmitResult | null
}

export default function ResultPanel({ queryResult, submitResult }: Props) {
  // 定义一个统一的容器样式，确保无论是否有数据，外观都是圆润的卡片
  const containerClass = "h-full w-full bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col relative"

  // 1. 空状态 (Empty State)
  if (!queryResult && !submitResult) {
    return (
      <div className="h-full p-3">
        <div className={containerClass}>
          {/* 使用 flex 居中显示空状态内容 */}
          <div className="flex-1 flex flex-col items-center justify-center text-gray-300">
             <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4 border border-gray-100">
                <svg className="w-8 h-8 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
             </div>
             <span className="text-xs font-bold uppercase tracking-widest opacity-60">Ready to Run</span>
             <p className="text-[11px] text-gray-400 mt-1 font-medium">Execute a query to see results here</p>
          </div>
        </div>
      </div>
    )
  }

  // 2. 有数据状态 (Data State)
  return (
    <div className="h-full flex flex-col p-3">
      {/* 提交反馈 (Floating Banner) */}
      {submitResult && (
        <div className="shrink-0 mb-3 animate-fade-in-up z-10">
          <div
            className={`flex items-start gap-3 p-3.5 rounded-2xl border shadow-sm ${
              submitResult.correct 
                ? 'bg-green-50/80 border-green-100 text-green-900' 
                : 'bg-red-50/80 border-red-100 text-red-900'
            }`}
          >
            <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${submitResult.correct ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'}`}>
              {submitResult.correct ? (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
              )}
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold mb-0.5">{submitResult.correct ? 'Correct Answer' : 'Incorrect Answer'}</h4>
              <p className="text-xs opacity-90 leading-relaxed font-medium">{submitResult.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* 结果表格容器 (使用与空状态相同的 containerClass) */}
      {queryResult && (
        <div className={`${containerClass} animate-fade-in`}>
          {queryResult.error ? (
            // Error State
            <div className="flex-1 p-6 bg-red-50/30 flex flex-col items-center justify-center text-center">
               <div className="w-12 h-12 bg-red-100 text-red-500 rounded-full flex items-center justify-center mb-4">
                 <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
               </div>
               <h3 className="text-sm font-bold text-red-800 uppercase tracking-wide mb-2">Execution Error</h3>
               <pre className="font-mono text-red-600 text-xs whitespace-pre-wrap bg-white px-4 py-3 rounded-xl border border-red-100 shadow-sm max-w-full text-left">
                 {queryResult.error}
               </pre>
            </div>
          ) : (
            // Table State
            <>
              {/* Stat Bar */}
              <div className="h-10 shrink-0 flex items-center justify-between px-4 bg-gray-50/80 border-b border-gray-100 backdrop-blur-sm">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Query Result</span>
                <span className="px-2 py-0.5 rounded-full bg-gray-200/50 text-[10px] font-bold text-gray-500 border border-gray-200">
                  {queryResult.rows.length} Rows
                </span>
              </div>
              
              {/* Table */}
              <div className="flex-1 overflow-auto custom-scrollbar bg-white">
                <table className="min-w-full text-left text-sm whitespace-nowrap">
                  <thead className="sticky top-0 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.02)] z-10">
                    <tr>
                      {queryResult.columns.map((c, i) => (
                        <th key={i} className="px-5 py-3 text-xs font-bold text-gray-500 border-b border-gray-100 bg-gray-50/30">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {queryResult.rows.map((r, ri) => (
                      <tr key={ri} className="hover:bg-blue-50/30 transition-colors group">
                        {r.map((c, ci) => (
                          <td key={ci} className="px-5 py-2.5 text-gray-600 font-mono text-[11px]">
                            {c === null ? <span className="text-gray-300 italic">null</span> : String(c)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}