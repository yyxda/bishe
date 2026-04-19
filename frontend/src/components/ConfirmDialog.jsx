import React from 'react'
import './ConfirmDialog.css'

/**
 * 确认对话框组件。
 *
 * 用于替代浏览器默认的confirm对话框，与系统UI风格保持一致。
 */
export default class ConfirmDialog extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      isOpen: false,
      title: '',
      message: '',
      confirmText: '确定',
      cancelText: '取消',
      type: 'default', // default | warning | danger
      onConfirm: null,
      onCancel: null,
    }

    // 绑定全局实例
    ConfirmDialog.instance = this
    
    // 追踪 mousedown 是否发生在 overlay 上，用于防止文本选择时意外关闭
    this.mouseDownOnOverlay = false
  }

  /**
   * 处理遮罩层 mousedown 事件。
   * @param {MouseEvent} e 鼠标事件
   */
  handleOverlayMouseDown = (e) => {
    // 只有直接点击 overlay 才标记
    if (e.target === e.currentTarget) {
      this.mouseDownOnOverlay = true
    }
  }

  /**
   * 处理遮罩层点击事件，只有当 mousedown 和 click 都发生在 overlay 上时才关闭。
   * @param {MouseEvent} e 鼠标事件
   */
  handleOverlayClick = (e) => {
    // 只有当 mousedown 和 click 都发生在 overlay 上时才关闭对话框
    if (this.mouseDownOnOverlay && e.target === e.currentTarget) {
      const { onCancel } = this.state
      if (onCancel) {
        onCancel()
      }
    }
    this.mouseDownOnOverlay = false
  }

  /**
   * 打开确认对话框。
   * @param {object} options 对话框配置选项
   * @returns {Promise<boolean>} 用户选择结果
   */
  open(options) {
    return new Promise((resolve) => {
      this.setState({
        isOpen: true,
        title: options.title || '确认操作',
        message: options.message || '',
        confirmText: options.confirmText || '确定',
        cancelText: options.cancelText || '取消',
        type: options.type || 'default',
        onConfirm: () => {
          this.setState({ isOpen: false })
          resolve(true)
        },
        onCancel: () => {
          this.setState({ isOpen: false })
          resolve(false)
        },
      })
    })
  }

  /**
   * 静态方法：显示确认对话框。
   * @param {object} options 对话框配置选项
   * @returns {Promise<boolean>} 用户选择结果
   */
  static confirm(options) {
    if (ConfirmDialog.instance) {
      return ConfirmDialog.instance.open(options)
    }
    return Promise.resolve(false)
  }

  /**
   * 静态方法：显示删除确认对话框。
   * @param {string} itemName 要删除的项目名称
   * @returns {Promise<boolean>} 用户选择结果
   */
  static confirmDelete(itemName) {
    return ConfirmDialog.confirm({
      title: '确认删除',
      message: `确定要删除"${itemName}"吗？此操作无法撤销。`,
      confirmText: '删除',
      cancelText: '取消',
      type: 'danger',
    })
  }

  /**
   * 获取对话框图标。
   * @returns {JSX.Element} 图标元素
   */
  getIcon() {
    const { type } = this.state

    if (type === 'danger') {
      return (
        <div className="dialog-icon danger">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14" />
          </svg>
        </div>
      )
    }

    if (type === 'warning') {
      return (
        <div className="dialog-icon warning">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
      )
    }

    return (
      <div className="dialog-icon default">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </div>
    )
  }

  /**
   * 渲染组件。
   * @returns {JSX.Element | null} 组件结构
   */
  render() {
    const { isOpen, title, message, confirmText, cancelText, type, onConfirm, onCancel } = this.state

    if (!isOpen) {
      return null
    }

    return (
      <div 
        className="confirm-dialog-overlay" 
        onMouseDown={this.handleOverlayMouseDown}
        onClick={this.handleOverlayClick}
      >
        <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
          <div className="confirm-dialog-content">
            {this.getIcon()}
            <div className="confirm-dialog-text">
              <h3 className="confirm-dialog-title">{title}</h3>
              <p className="confirm-dialog-message">{message}</p>
            </div>
          </div>
          <div className="confirm-dialog-actions">
            <button className="btn-secondary" onClick={onCancel}>
              {cancelText}
            </button>
            <button className={`btn-confirm ${type}`} onClick={onConfirm}>
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    )
  }
}