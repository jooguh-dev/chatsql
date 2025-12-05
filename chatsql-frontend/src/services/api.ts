import axios from 'axios'
import type { DatabaseSchema, Exercise, QueryResult, SubmitResult, AIResponse } from '../types'

// 使用相对路径，通过Vite proxy转发，避免跨域问题
// 如果设置了VITE_API_BASE_URL环境变量，则使用它；否则使用相对路径通过proxy
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // 确保cookie被发送
})

// --- Mock data ---
const mockSchemas: DatabaseSchema[] = [
  {
    id: 1,
    name: 'employees',
    display_name: 'Employees DB',
    description: 'Demo employees schema',
    exercise_count: 3,
  },
]

const mockExercises: Exercise[] = [
  {
    id: 1,
    title: 'Two Sum (SQL demo)',
    description: 'Find pairs of employees in the same department.',
    difficulty: 'easy',
    initial_query: 'SELECT id, name, dept FROM employees',
    hints: [{ level: 1, text: 'Start with a simple SELECT' }],
    schema: { id: 1, name: 'employees', display_name: 'Employees DB', db_name: 'employees' },
    tags: ['select', 'join'],
  },
  {
    id: 2,
    title: 'Count by Department',
    description: 'Count number of employees per department.',
    difficulty: 'easy',
    initial_query: 'SELECT dept, COUNT(*) FROM employees GROUP BY dept',
    hints: [],
    schema: { id: 1, name: 'employees', display_name: 'Employees DB', db_name: 'employees' },
    tags: ['aggregate'],
  },
  {
    id: 3,
    title: 'Top Salaries',
    description: 'Find employees with highest salaries in each department.',
    difficulty: 'medium',
    initial_query: 'SELECT * FROM employees',
    hints: [],
    schema: { id: 1, name: 'employees', display_name: 'Employees DB', db_name: 'employees' },
    tags: ['window', 'join'],
  },
]

const mockQueryResult: QueryResult = {
  success: true,
  columns: ['id', 'name', 'dept'],
  rows: [
    [1, 'Alice', 'Engineering'],
    [2, 'Bob', 'Engineering'],
    [3, 'Carol', 'HR'],
  ],
  row_count: 3,
  execution_time: 12,
}

const mockSubmitResult: SubmitResult = {
  correct: true,
  message: 'All tests passed (mock).',
  user_result: mockQueryResult,
}

const mockAIResponse: AIResponse = {
  response:
    "Based on your question, here's what I found: You have completed 3 exercises this month. (mock data)",
  sql_query:
    "SELECT COUNT(*) FROM submissions WHERE user_id=1 AND status='correct' AND MONTH(created_at)=MONTH(CURRENT_DATE)",
  query_result: {
    success: true,
    columns: ['count'],
    rows: [[3]],
    row_count: 1,
  },
  executed: true,
  intent: 'data_query',
}

// --- Helpers ---
async function tryApi<T>(fn: () => Promise<T>, fallback: T, useMock: boolean): Promise<T> {
  if (useMock) return Promise.resolve(fallback)
  try {
    const result = await fn()
    console.log('API call successful:', result)
    return result
  } catch (e: any) {
    console.error('API call failed, falling back to mock data', e)
    console.error('Error details:', {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status,
      url: e.config?.url
    })
    return fallback
  }
}

export const getSchemas = async (useMock = false): Promise<DatabaseSchema[]> => {
  return tryApi(
    async () => {
      const r = await api.get('/schemas/')
      return r.data
    },
    mockSchemas,
    useMock
  )
}

export const getExercises = async (useMock = false, params?: any): Promise<Exercise[]> => {
  return tryApi(
    async () => {
      const r = await api.get('/exercises/', { params })
      return r.data
    },
    mockExercises,
    useMock
  )
}

export const getExercise = async (id: number, useMock = false): Promise<Exercise> => {
  return tryApi(
    async () => {
      const r = await api.get(`/exercises/${id}/`)
      console.log('Exercise detail API response:', r.data)
      return r.data
    },
    mockExercises.find((e) => e.id === id) || mockExercises[0],
    useMock
  )
}

export const executeQuery = async (
  exerciseId: number,
  query: string,
  useMock = false
): Promise<QueryResult> => {
  return tryApi(
    async () => {
      const r = await api.post(`/exercises/${exerciseId}/execute/`, { query })
      return r.data
    },
    { ...mockQueryResult, rows: mockQueryResult.rows },
    useMock
  )
}

export const submitQuery = async (
  exerciseId: number,
  query: string,
  useMock = false
): Promise<SubmitResult> => {
  return tryApi(
    async () => {
      const r = await api.post(`/exercises/${exerciseId}/submit/`, { query })
      return r.data
    },
    mockSubmitResult,
    useMock
  )
}

export const getAIResponse = async (
  exerciseId: number,
  message: string,
  userQuery?: string,
  error?: string,
  useMock = false,
  submissions?: Submission[]
): Promise<AIResponse> => {
  return tryApi(
    async () => {
      const r = await api.post(`/exercises/${exerciseId}/ai/`, {
        message,
        user_query: userQuery,
        error,
        submissions: submissions || [],
      })
      return r.data
    },
    mockAIResponse,
    useMock
  )
}

export interface Submission {
  id: number
  query: string
  status: 'correct' | 'incorrect'
  execution_time: number | null
  created_at: string
  updated_at: string
}

export const getSubmissions = async (
  exerciseId: number,
  useMock = false
): Promise<Submission[]> => {
  if (useMock) {
    return []
  }
  
  try {
    console.log(`[getSubmissions] Fetching submissions for exerciseId=${exerciseId}`)
    const r = await api.get(`/exercises/${exerciseId}/submissions/`)
    console.log(`[getSubmissions] Response:`, r.data)
    console.log(`[getSubmissions] Found ${r.data.length} submissions`)
    return r.data
  } catch (e: any) {
    console.error('[getSubmissions] Failed to fetch submissions:', e)
    console.error('[getSubmissions] Error details:', {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status,
    })
    // 如果是401错误，说明用户未登录
    if (e.response?.status === 401) {
      console.warn('[getSubmissions] User not authenticated')
    }
    return []
  }
}

// Instructor APIs
export const getInstructorStats = async () => {
  const r = await api.get('/instructor/stats/')
  return r.data
}

export const getInstructorStudents = async () => {
  const r = await api.get('/instructor/students/')
  return r.data
}

export const getInstructorRecentActivity = async () => {
  const r = await api.get('/instructor/recent-activity/')
  return r.data
}

export const getInstructorExercises = async () => {
  const r = await api.get('/instructor/exercises/')
  return r.data
}

export const createExercise = async (data: {
  title: string
  description: string
  difficulty: string
  initial_query?: string
  answer_query: string
  schema_id: number
}) => {
  const r = await api.post('/instructor/exercises/', {
    title: data.title,
    description: data.description,
    difficulty: data.difficulty.toLowerCase(),
    schema_id: data.schema_id,
    expected_sql: data.answer_query,
    initial_query: data.initial_query || ''
  })
  return r.data
}

export const updateExercise = async (id: number, data: any) => {
  const r = await api.put(`/instructor/exercises/${id}/`, data)
  return r.data
}

export const deleteExercise = async (id: number) => {
  const r = await api.delete(`/instructor/exercises/${id}/`)
  return r.data
}

export default api
