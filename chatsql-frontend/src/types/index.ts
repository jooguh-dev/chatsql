export interface DatabaseSchema {
  id: number
  name: string
  display_name: string
  description?: string
  db_name?: string
  exercise_count?: number
}

export interface Exercise {
  id: number
  title: string
  description: string
  difficulty: 'easy' | 'medium' | 'hard'
  initial_query?: string
  expected_query?: string  // Solution SQL query
  hints?: { level: number; text: string }[]
  schema: DatabaseSchema
  tags?: string[]
  workshop?: string
  database_name?: string
}

export interface QueryResult {
  success: boolean
  columns: string[]
  rows: any[][]
  row_count: number
  execution_time?: number
  error?: string
}

export interface SubmitResult {
  correct: boolean
  message: string
  user_result?: QueryResult
  expected_result?: QueryResult
  feedback?: string
}

export interface AIResponse {
  response: string
  sql_query?: string
  query_result?: {
    success: boolean
    columns: string[]
    rows: any[][]
    row_count: number
  }
  executed?: boolean
  intent?: string
  execution_error?: string
}
