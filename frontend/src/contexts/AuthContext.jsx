/**
 * 认证上下文模块。
 *
 * 提供全局认证状态管理，包括登录、登出、令牌刷新等功能。
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

/**
 * 认证上下文。
 */
const AuthContext = createContext(null)

/**
 * 本地存储键名常量。
 */
const STORAGE_KEYS = {
  TOKEN: 'token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
}

/**
 * 认证状态提供者组件。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 认证上下文提供者
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  /**
   * 初始化时从本地存储恢复认证状态。
   */
  useEffect(() => {
    const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN)
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER)

    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch (error) {
        console.error('解析用户信息失败:', error)
        clearAuth()
      }
    }
    setIsLoading(false)
  }, [])

  /**
   * 清除认证状态。
   */
  const clearAuth = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    setToken(null)
    setUser(null)
  }, [])

  /**
   * 登录成功后保存认证状态。
   *
   * @param {object} loginData 登录响应数据
   */
  const login = useCallback((loginData) => {
    const { token: accessToken, refresh_token, user_id, student_id, display_name, role, email_account_id } = loginData

    localStorage.setItem(STORAGE_KEYS.TOKEN, accessToken)
    if (refresh_token) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh_token)
    }

    const userData = {
      userId: user_id,
      studentId: student_id,
      displayName: display_name,
      role: role || 'user',
      emailAccountId: email_account_id,
    }
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData))

    setToken(accessToken)
    setUser(userData)
  }, [])

  /**
   * 登出清除认证状态。
   */
  const logout = useCallback(() => {
    clearAuth()
  }, [clearAuth])

  /**
   * 判断是否已认证。
   */
  const isAuthenticated = Boolean(token && user)

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * 获取认证上下文的Hook。
 *
 * @returns {object} 认证上下文值
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext