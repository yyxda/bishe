/**
 * 登录页面组件。
 *
 * 提供学生邮箱登录和管理员登录两种方式。
 */

import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'
import AuthService from '../services/AuthService.js'
import FormValidator from '../utils/FormValidator.js'
import Toast from '../components/Toast.jsx'

/**
 * 登录页面。
 *
 * @returns {JSX.Element} 登录页面结构
 */
export default function LoginPage() {
  const [loginType, setLoginType] = useState('student')
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [emailType, setEmailType] = useState('qq')
  const [authCode, setAuthCode] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  const { login } = useAuth()
  const navigate = useNavigate()

  const validator = new FormValidator()
  const authService = AuthService.createDefault()

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault()

      if (status === 'loading') {
        return
      }

      setStatus('loading')
      setMessage('正在验证账号信息...')

      try {
        // 先检查系统健康状态
        const healthResponse = await fetch('/api/health')
        if (!healthResponse.ok) {
          throw new Error('后端服务不可用，请检查后端是否启动')
        }

        let response
        if (loginType === 'admin') {
          response = await authService.login(studentId, password, '', '')
        } else {
          response = await authService.login(studentId, '', emailType, authCode)
        }

        if (response.success) {
          setStatus('success')
          setMessage('登录成功。')

          login({
            token: response.token,
            refresh_token: response.refresh_token,
            user_id: response.user_id,
            student_id: response.student_id,
            display_name: response.display_name,
            role: response.role,
          })

          Toast.success('登录成功，欢迎回来！')

          const role = response.role || 'user'
          if (role === 'super_admin' || role === 'admin') {
            navigate('/admin', { replace: true })
          } else {
            navigate('/mail', { replace: true })
          }
          return
        }

        setStatus('error')
        setMessage(response.message || '账号或密码错误。')
      } catch (error) {
        let errorMessage = '服务器暂时不可用，请稍后重试。'

        if (error?.message) {
          if (
            error.message.includes('Failed to fetch') ||
            error.message.includes('NetworkError')
          ) {
            errorMessage = '网络连接失败，请检查网络后重试。'
          } else if (error.message.includes('timeout')) {
            errorMessage = '请求超时，服务器响应过慢。'
          } else if (error.message.includes('后端服务不可用')) {
            errorMessage = '后端服务未启动，请检查后端服务状态。'
          } else {
            errorMessage = error.message
          }
        }

        setStatus('error')
        setMessage(errorMessage)
        
        // 显示详细的错误信息
        Toast.error(errorMessage)
      }
    },
    [studentId, password, authCode, emailType, loginType, status, login, navigate, authService]
  )

  const isLoading = status === 'loading'

  return (
    <div className="app">
      <main className="login-shell">
        <section className="brand-panel">
          <span className="brand-badge">邮箱智能防护</span>
          <h1>钓鱼邮件智能检测系统</h1>
          <p>基于机器学习的邮件钓鱼邮件检测系统，让每一次登录都更安全。</p>
          <div className="feature-list">
            <div className="feature-item">
              <span>01</span>
              <div>
                <h3>实时威胁感知</h3>
                <p>多维特征融合，快速拦截可疑邮件。</p>
              </div>
            </div>
            <div className="feature-item">
              <span>02</span>
              <div>
                <h3>行为模型驱动</h3>
                <p>账号行为画像，识别异常登录。</p>
              </div>
            </div>
            <div className="feature-item">
              <span>03</span>
              <div>
                <h3>高并发架构</h3>
                <p>Router-Service-CRUD 分层，支撑高峰访问。</p>
              </div>
            </div>
          </div>
        </section>

        <section className="login-card">
          <header>
            <h2>邮箱助手</h2>
            <div className="login-type-switch">
              <button
                type="button"
                className={loginType === 'student' ? 'active' : ''}
                onClick={() => {
                  setLoginType('student')
                  setMessage('')
                }}
              >
                用户登录
              </button>
              <button
                type="button"
                className={loginType === 'admin' ? 'active' : ''}
                onClick={() => {
                  setLoginType('admin')
                  setMessage('')
                }}
              >
                管理员测试登录
              </button>
            </div>
            <p>{loginType === 'student' ? '请输入邮箱账号与授权码，快速登录。' : '请输入管理员账号与密码。'}</p>
          </header>

          <form onSubmit={handleSubmit} className="login-form">
            {loginType === 'student' ? (
              <>
                <label className="form-row">
                  <span>邮箱类型</span>
                  <select
                    name="emailType"
                    value={emailType}
                    onChange={(e) => {
                      setEmailType(e.target.value)
                      setMessage('')
                    }}
                    disabled={isLoading}
                  >
                    <option value="qq">QQ邮箱</option>
                    <option value="163">163邮箱</option>
                    <option value="126">126邮箱</option>
                    <option value="netease">网易邮箱</option>
                  </select>
                </label>

                <label className="form-row">
                  <span>邮箱账号</span>
                  <input
                    name="email"
                    type="text"
                    autoComplete="username"
                    placeholder="your@email.com"
                    value={studentId}
                    onChange={(e) => {
                      setStudentId(e.target.value)
                      setMessage('')
                    }}
                    disabled={isLoading}
                  />
                </label>

                <label className="form-row">
                  <span>授权码</span>
                  <input
                    name="authCode"
                    type="text"
                    autoComplete="off"
                    placeholder="请输入邮箱授权码"
                    value={authCode}
                    onChange={(e) => {
                      setAuthCode(e.target.value)
                      setMessage('')
                    }}
                    disabled={isLoading}
                  />
                </label>
              </>
            ) : (
              <>
                <label className="form-row">
                  <span>管理员账号</span>
                  <input
                    name="adminId"
                    type="text"
                    autoComplete="username"
                    placeholder="Administrator"
                    value={studentId}
                    onChange={(e) => {
                      setStudentId(e.target.value)
                      setMessage('')
                    }}
                    disabled={isLoading}
                  />
                </label>

                <label className="form-row">
                  <span>密码</span>
                  <input
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="请输入管理员密码"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value)
                      setMessage('')
                    }}
                    disabled={isLoading}
                  />
                </label>
              </>
            )}

            {message && (
              <div className={`status status-${status}`} role="status">
                {message}
              </div>
            )}

            <button type="submit" disabled={isLoading}>
              {isLoading ? '验证中...' : '登录'}
            </button>
          </form>

          <footer>
            <p>{loginType === 'student' ? '只支持邮箱授权码登录，无需其他信息。' : '管理员账号密码登录。'}</p>
          </footer>
        </section>
      </main>
    </div>
  )
}