/**
 * 侧边栏组件。
 *
 * 显示用户信息、邮箱账户列表和操作按钮。
 */

import React from 'react'

/**
 * 侧边栏组件。
 *
 * @param {object} props 组件属性
 * @returns {JSX.Element} 侧边栏结构
 */
export default function Sidebar({
  user,
  accounts,
  selectedAccountId,
  selectedFolder,
  isLoading,
  isSyncing,
  onSelectAccount,
  onSelectFolder,
  onSyncEmails,
  onDeleteAccount,
  onAddEmail,
  onCompose,
  onRedetectEmails,
  onManageWhitelist,
  onLogout,
}) {
  return (
    <aside className="mail-sidebar">
      <div className="sidebar-header">
        <div className="user-info">
          <div className="user-avatar">{user?.displayName?.[0] || 'U'}</div>
          <div className="user-details">
            <span className="user-name">{user?.displayName || '用户'}</span>
            <span className="user-id">{user?.studentId}</span>
          </div>
        </div>
        <button className="btn-logout" onClick={onLogout} title="退出登录">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
          </svg>
        </button>
      </div>

      <div className="sidebar-actions">
        <button className="btn-primary" onClick={onCompose}>
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          写邮件
        </button>
        <button className="btn-secondary" onClick={onRedetectEmails} title="重新检测邮件">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 11-9-9" />
          </svg>
          重新检测
        </button>
        <button className="btn-secondary" onClick={onManageWhitelist} title="白名单管理">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          白名单
        </button>
      </div>

      <nav className="account-list">
        <div className="account-list-header">
          <span>邮件文件夹</span>
        </div>

        <button
          className={`account-item ${selectedFolder === 'inbox' ? 'active' : ''}`}
          onClick={() => onSelectFolder('inbox')}
        >
          <span className="account-icon">📥</span>
          <span className="account-name">收件箱</span>
        </button>

        <button
          className={`account-item ${selectedFolder === 'phishing' ? 'active' : ''}`}
          onClick={() => onSelectFolder('phishing')}
        >
          <span className="account-icon">⚠️</span>
          <span className="account-name">钓鱼邮件</span>
        </button>

        <div className="account-list-header" style={{ marginTop: '20px' }}>
          <span>邮箱账户</span>
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <button className="btn-icon" onClick={onAddEmail} title="添加邮箱">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="loading-placeholder">加载中...</div>
        ) : (
          <>
            <button
              className={`account-item ${selectedAccountId === null ? 'active' : ''}`}
              onClick={() => onSelectAccount(null)}
            >
              <span className="account-icon">📨</span>
              <span className="account-name">全部邮箱</span>
            </button>

            {accounts.map((account) => (
              <div key={account.id} className="account-item-wrapper">
                <button
                  className={`account-item ${selectedAccountId === account.id ? 'active' : ''}`}
                  onClick={() => onSelectAccount(account.id)}
                >
                  <span className="account-icon">
                    {account.email_type === 'QQ' ? '📨' : account.email_type === 'NETEASE' ? '📧' : '✉️'}
                  </span>
                  <span className="account-name">{account.email_address}</span>
                </button>
                <div className="account-actions">
                  <button
                    className="btn-icon-sm"
                    onClick={() => onSyncEmails(account.id)}
                    disabled={isSyncing}
                    title="同步邮件"
                  >
                    <svg
                      className={isSyncing ? 'spin' : ''}
                      viewBox="0 0 24 24"
                      width="14"
                      height="14"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 12a9 9 0 11-9-9" />
                    </svg>
                  </button>
                  <button
                    className="btn-icon-sm btn-danger"
                    onClick={() => onDeleteAccount(account.id, account.email_address)}
                    title="删除邮箱"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </>
        )}
      </nav>
    </aside>
  )
}