/**
 * 应用根组件。
 *
 * 配置路由系统和认证状态管理。
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx'
import './App.css'
import LoginPage from './pages/LoginPage.jsx'
import MailClientPage from './pages/MailClientPage/index.jsx'
import AdminPage from './pages/AdminPage/index.jsx'
import DirectDetectPage from './pages/DirectDetectPage/index.jsx'
import Toast from './components/Toast.jsx'
import ConfirmDialog from './components/ConfirmDialog.jsx'

/**
 * 学生路由组件（限制管理员访问邮件页面）。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 路由元素
 */
function StudentRoute({ children }) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // 管理员不能访问邮件页面，重定向到管理后台
  const role = user?.role || 'user'
  if (role === 'super_admin' || role === 'admin') {
    return <Navigate to="/admin" replace />
  }

  return children
}

/**
 * 公开路由组件（已登录用户重定向）。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 路由元素
 */
function PublicRoute({ children }) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (isAuthenticated) {
    // 根据角色重定向到正确页面
    const role = user?.role || 'user'
    if (role === 'super_admin' || role === 'admin') {
      return <Navigate to="/admin" replace />
    }
    return <Navigate to="/mail" replace />
  }

  return children
}

/**
 * 管理员路由组件（限制普通用户访问）。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 路由元素
 */
function AdminRoute({ children }) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // 普通用户无法访问管理员页面
  const role = user?.role || 'user'
  if (role === 'user') {
    return <Navigate to="/mail" replace />
  }

  return children
}

/**
 * 应用路由配置。
 *
 * @returns {JSX.Element} 路由结构
 */
function AppRoutes() {
  const { isAuthenticated, user } = useAuth()

  // 首页根据角色跳转
  const getHomePath = () => {
    if (!isAuthenticated) return '/login'
    const role = user?.role || 'user'
    if (role === 'super_admin' || role === 'admin') return '/admin'
    return '/mail'
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/mail"
        element={
          <StudentRoute>
            <MailClientPage />
          </StudentRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminPage />
          </AdminRoute>
        }
      />
      <Route
        path="/direct-detect"
        element={
          <AdminRoute>
            <DirectDetectPage />
          </AdminRoute>
        }
      />
      <Route
        path="/"
        element={<Navigate to={getHomePath()} replace />}
      />
    </Routes>
  )
}

/**
 * 应用主组件。
 *
 * @returns {JSX.Element} 应用结构
 */
function App() {
  return (
    <AuthProvider>
      <Toast />
      <ConfirmDialog />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App