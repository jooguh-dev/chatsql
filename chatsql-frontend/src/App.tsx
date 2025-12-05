import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Layout from './components/Layout'
import AuthPage from './pages/AuthPage'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import InstructorLayout from './components/InstructorLayout'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public homepage */}
          <Route path="/" element={<Layout />} />

          {/* Public login/signup page */}
          <Route path="/auth" element={<AuthPage />} />

          <Route path="/instructor" element={<InstructorLayout />} />
          {/* ProtectedRoute */}
          {/*
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
