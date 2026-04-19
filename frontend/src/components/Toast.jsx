import React from 'react'
import './Toast.css'

/**
 * Toast消息类型枚举。
 */
export const ToastType = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
}

/**
 * Toast通知组件。
 *
 * 用于显示系统通知消息，替代浏览器默认的alert。
 */
export default class Toast extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      toasts: [],
    }

    // 绑定全局实例
    Toast.instance = this
  }

  /**
   * 添加新的Toast消息。
   * @param {string} message 消息内容
   * @param {string} type 消息类型
   * @param {number} duration 显示时长（毫秒）
   */
  addToast(message, type = ToastType.INFO, duration = 3000) {
    const id = Date.now() + Math.random()
    const toast = { id, message, type, duration }

    this.setState((prevState) => ({
      toasts: [...prevState.toasts, toast],
    }))

    // 自动移除
    if (duration > 0) {
      setTimeout(() => {
        this.removeToast(id)
      }, duration)
    }
  }

  /**
   * 移除Toast消息。
   * @param {number} id Toast ID
   */
  removeToast(id) {
    this.setState((prevState) => ({
      toasts: prevState.toasts.filter((t) => t.id !== id),
    }))
  }

  /**
   * 静态方法：显示成功消息。
   * @param {string} message 消息内容
   * @param {number} duration 显示时长
   */
  static success(message, duration = 3000) {
    if (Toast.instance) {
      Toast.instance.addToast(message, ToastType.SUCCESS, duration)
    }
  }

  /**
   * 静态方法：显示错误消息。
   * @param {string} message 消息内容
   * @param {number} duration 显示时长
   */
  static error(message, duration = 4000) {
    if (Toast.instance) {
      Toast.instance.addToast(message, ToastType.ERROR, duration)
    }
  }

  /**
   * 静态方法：显示警告消息。
   * @param {string} message 消息内容
   * @param {number} duration 显示时长
   */
  static warning(message, duration = 3500) {
    if (Toast.instance) {
      Toast.instance.addToast(message, ToastType.WARNING, duration)
    }
  }

  /**
   * 静态方法：显示信息消息。
   * @param {string} message 消息内容
   * @param {number} duration 显示时长
   */
  static info(message, duration = 3000) {
    if (Toast.instance) {
      Toast.instance.addToast(message, ToastType.INFO, duration)
    }
  }

  /**
   * 获取Toast图标。
   * @param {string} type 消息类型
   * @returns {JSX.Element} 图标元素
   */
  getIcon(type) {
    switch (type) {
      case ToastType.SUCCESS:
        return (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        )
      case ToastType.ERROR:
        return (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        )
      case ToastType.WARNING:
        return (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        )
      default:
        return (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        )
    }
  }

  /**
   * 渲染组件。
   * @returns {JSX.Element} 组件结构
   */
  render() {
    const { toasts } = this.state

    if (toasts.length === 0) {
      return null
    }

    return (
      <div className="toast-container">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast toast-${toast.type}`}
            onClick={() => this.removeToast(toast.id)}
          >
            <span className="toast-icon">{this.getIcon(toast.type)}</span>
            <span className="toast-message">{toast.message}</span>
            <button className="toast-close" onClick={() => this.removeToast(toast.id)}>
              ×
            </button>
          </div>
        ))}
      </div>
    )
  }
}
