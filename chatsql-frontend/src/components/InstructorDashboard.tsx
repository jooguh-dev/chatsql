import React, { useEffect, useState } from 'react'
import { getInstructorStats, getInstructorRecentActivity } from '../services/api'

const StatCard = ({ title, value, trend }: { title: string; value: string; trend: string }) => (
  <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col gap-2 hover:shadow-md transition-shadow">
    <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">{title}</span>
    <div className="text-3xl font-bold text-gray-900 tracking-tight">{value}</div>
    <div className="flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full w-fit border border-emerald-100">
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
      {trend}
    </div>
  </div>
)

export default function InstructorDashboard() {
  const [stats, setStats] = useState({
    total_students: 0,
    total_exercises: 0,
    total_submissions: 0,
    average_completion_rate: 0
  })
  const [recentActivity, setRecentActivity] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsData, activityData] = await Promise.all([
          getInstructorStats(),
          getInstructorRecentActivity()
        ])
        setStats(statsData)
        setRecentActivity(activityData)
      } catch (err) {
        console.error('Failed to load instructor data:', err)
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* 1. Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Students" 
          value={stats.total_students.toString()} 
          trend={`${stats.total_students} Active`} 
        />
        <StatCard 
          title="Active Exercises" 
          value={stats.total_exercises.toString()} 
          trend={`${stats.total_exercises} Total`} 
        />
        <StatCard 
          title="Avg. Completion" 
          value={`${stats.average_completion_rate}%`} 
          trend={`${stats.total_submissions} Submissions`} 
        />
      </div>

      {/* 2. Recent Activity Table */}
      <div className="bg-white rounded-3xl border border-gray-200 shadow-sm flex flex-col overflow-hidden">
        <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h3 className="font-bold text-gray-800">Recent Activity</h3>
          <button className="text-xs font-bold text-gray-400 hover:text-gray-900 uppercase tracking-wide">View All</button>
        </div>
        
        <div className="overflow-x-auto">
          {recentActivity.length === 0 ? (
            <div className="px-8 py-12 text-center text-gray-400">
              No recent activity yet
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-white text-gray-400 border-b border-gray-100">
                <tr>
                  <th className="px-8 py-3 font-semibold text-[11px] uppercase tracking-wider">User</th>
                  <th className="px-8 py-3 font-semibold text-[11px] uppercase tracking-wider">Action</th>
                  <th className="px-8 py-3 font-semibold text-[11px] uppercase tracking-wider">Date</th>
                  <th className="px-8 py-3 font-semibold text-[11px] uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentActivity.map((activity) => (
                  <tr key={activity.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-8 py-4 font-medium text-gray-900 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-xs text-gray-600 font-bold">
                        {activity.user.charAt(0).toUpperCase()}
                      </div>
                      {activity.user}
                    </td>
                    <td className="px-8 py-4 text-gray-600">{activity.action}</td>
                    <td className="px-8 py-4 text-gray-400 text-xs">
                      {new Date(activity.date).toLocaleString()}
                    </td>
                    <td className="px-8 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                        activity.status === 'correct' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {activity.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}