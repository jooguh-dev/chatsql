import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

interface ProtectedRouteProps {
  children: React.ReactElement
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // loading
  if (isLoading) {
    return <div style={{ padding: '1rem' }}>Loading...</div>
  }

  // user is NOT authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace state={{ from: location }} />
  }

  // user IS authenticated
  return children
}

export default ProtectedRoute
