import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

// 引入子组件
import AIChat from './AIChat'
import InstructorDashboard from './InstructorDashboard'
import StudentManager from './StudentManager'
import ExerciseManager from './ExerciseManager'

// 菜单配置
const MENU_ITEMS = [
  { 
    id: 'dashboard', 
    label: 'Overview', 
    icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' 
  },
  { 
    id: 'students', 
    label: 'Students', 
    icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' 
  },
  { 
    id: 'exercises', 
    label: 'Exercises', 
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' 
  },
]

// 侧边栏菜单项组件
const MenuItem = ({ item, isActive, onClick }: { item: any; isActive: boolean; onClick: () => void }) => (
  <div
    onClick={onClick}
    className={`
      group flex items-center gap-3 px-4 py-2.5 mx-2 mb-1 rounded-lg cursor-pointer text-sm font-medium transition-all
      ${isActive 
        ? 'bg-gray-900 text-white shadow-md' 
        : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
      }
    `}
  >
    <svg className={`w-4 h-4 ${isActive ? 'text-gray-300' : 'text-gray-400 group-hover:text-gray-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
    </svg>
    <span>{item.label}</span>
  </div>
)

const InstructorLayout: React.FC = () => {
  const { isAuthenticated, username, setAuth } = useAuth()
  const navigate = useNavigate()

  // 状态管理
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isAIChatOpen, setIsAIChatOpen] = useState(true)

  const handleLogout = () => {
    if (setAuth) setAuth({ isAuthenticated: false, username: '', role: null })
    navigate('/auth')
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((e) => console.error(e))
    } else {
      if (document.exitFullscreen) document.exitFullscreen()
    }
  }

  return (
    <div className="h-screen w-screen bg-[#F0F2F5] p-4 flex items-center justify-center font-sans text-gray-900 overflow-hidden">
      
      {/* App Window Container */}
      <div className="w-full h-full max-w-[1920px] bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.12)] border border-gray-200 overflow-hidden flex relative transition-all">
        
        {/* 1️⃣ LEFT SIDEBAR (Menu) */}
        <aside 
          className={`
            flex-shrink-0 bg-[#F8F9FA] border-r border-gray-200 flex flex-col transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] overflow-hidden
            ${isSidebarOpen ? 'w-[260px] opacity-100' : 'w-0 opacity-0 border-none'}
          `}
        >
          {/* Header */}
          <div className="h-14 flex items-center justify-between px-6 shrink-0">
             <div className="flex items-center gap-2 group">
               {/* Traffic Lights (Function Controls) */}
               <button onClick={() => setIsSidebarOpen(false)} className="w-3 h-3 rounded-full bg-[#FF5F57] hover:bg-[#FF5F57]/80 border border-[#E05E58] shadow-sm transition-colors" title="Close Menu" />
               <button onClick={() => setIsAIChatOpen(!isAIChatOpen)} className="w-3 h-3 rounded-full bg-[#FEBC2E] hover:bg-[#FEBC2E]/80 border border-[#DFA023] shadow-sm transition-colors" title="Toggle Copilot" />
               <button onClick={toggleFullscreen} className="w-3 h-3 rounded-full bg-[#28C840] hover:bg-[#28C840]/80 border border-[#23AD37] shadow-sm transition-colors" title="Fullscreen" />
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-gray-200 text-gray-600 border border-gray-300 tracking-wide">
              ADMIN
            </span>
          </div>

          <div className="px-6 py-4">
             <h2 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Management</h2>
          </div>

          {/* Menu Items */}
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 px-2">
            {MENU_ITEMS.map(item => (
              <MenuItem 
                key={item.id} 
                item={item} 
                isActive={activeTab === item.id} 
                onClick={() => setActiveTab(item.id)}
              />
            ))}
          </div>

          {/* User Profile Footer */}
          <div className="p-4 bg-[#F8F9FA] border-t border-gray-200">
             <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer border border-transparent hover:border-gray-200">
               <div className="w-9 h-9 rounded-lg bg-gray-900 flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-sm">
                 {username ? username.charAt(0).toUpperCase() : 'A'}
               </div>
               <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-gray-800 truncate">{username || 'Instructor'}</div>
                  <div className="text-[10px] text-gray-500">Pro Access</div>
               </div>
               <button onClick={handleLogout} className="text-gray-400 hover:text-red-600 transition-colors" title="Logout">
                 <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
               </button>
             </div>
          </div>
        </aside>

        {/* 2️⃣ MAIN CONTENT (Dashboard / Data) */}
        <main className="flex-1 flex flex-col min-w-0 bg-white relative z-0">
          
          {/* Top Toolbar */}
          <div className="h-14 border-b border-gray-100 flex items-center px-6 shrink-0 justify-between bg-white z-20">
             <div className="flex items-center gap-4">
               {/* Show Sidebar Toggle (visible if closed) */}
               {!isSidebarOpen && (
                 <button onClick={() => setIsSidebarOpen(true)} className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
                   <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                 </button>
               )}
               
               {/* Breadcrumbs */}
               <div className="flex items-center gap-2 text-sm">
                 <span className="text-gray-400">Team</span>
                 <svg className="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                 <h2 className="font-bold text-gray-900 tracking-tight">
                   {MENU_ITEMS.find(i => i.id === activeTab)?.label}
                 </h2>
               </div>
             </div>

             {/* Show Copilot Toggle (visible if closed) */}
             {!isAIChatOpen && (
                <button 
                  onClick={() => setIsAIChatOpen(true)}
                  className="flex items-center gap-2 text-[11px] font-semibold text-gray-700 bg-gray-50 px-3 py-1.5 rounded-full hover:bg-gray-100 transition-colors border border-gray-200"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  Admin Copilot
                </button>
             )}
          </div>

          {/* Content Area - 动态渲染子组件 */}
          <div className="flex-1 overflow-y-auto bg-[#F9FAFB] p-8 custom-scrollbar">
             {activeTab === 'dashboard' && <InstructorDashboard />}
             {activeTab === 'students' && <StudentManager />}
             {activeTab === 'exercises' && <ExerciseManager />}
          </div>
        </main>

        {/* 3️⃣ RIGHT SIDEBAR (Admin Copilot) */}
        <aside 
          className={`
            flex-shrink-0 bg-[#F8F9FA] border-l border-gray-200 flex flex-col transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] overflow-hidden
            ${isAIChatOpen ? 'w-[340px] opacity-100' : 'w-0 opacity-0 border-none'}
          `}
        >
           {/* 复用 AI 组件，传递 onClose 允许内部关闭 */}
           <AIChat 
             exercise={null} 
             userQuery=""
             error={undefined}
             demoMode={false} 
             onClose={() => setIsAIChatOpen(false)}
           />
        </aside>

      </div>
    </div>
  )
}

export default InstructorLayout