/**
 * 邮件列表组件。
 *
 * 显示邮件列表，支持选择和钓鱼状态标记。
 */

import React from 'react'

/**
 * 邮件列表组件。
 *
 * @param {object} props 组件属性
 * @returns {JSX.Element} 邮件列表结构
 */
export default function EmailList({ emails, selectedEmail, isLoading, onSelectEmail, folderName = '收件箱' }) {
  return (
    <section className="email-list">
      <div className="email-list-header">
        <h2>{folderName}</h2>
        <span className="email-count">{emails.length} 封邮件</span>
      </div>

      <div className="email-list-content">
        {isLoading ? (
          <div className="loading-placeholder">加载中...</div>
        ) : emails.length === 0 ? (
          <div className="empty-placeholder">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
            <p>暂无邮件</p>
          </div>
        ) : (
          emails.map((email) => {
            const detectionStatus = (email.phishing_status || 'COMPLETED').toUpperCase()
            const isPending = detectionStatus !== 'COMPLETED'
            const displayLevel = (email.phishing_level || 'NORMAL').toUpperCase()
            const displayTag = isPending ? 'PENDING' : displayLevel
            return (
              <div
                key={email.id}
                className={`email-item ${selectedEmail?.id === email.id ? 'active' : ''} ${
                  !email.is_read ? 'unread' : ''
                } phishing-${displayTag.toLowerCase()}`}
                onClick={() => onSelectEmail(email)}
              >
                <div className="email-item-indicator">
                  {isPending && (
                    <span className="phishing-badge pending" title="钓鱼检测中">
                      ⏳
                    </span>
                  )}
                  {!isPending && displayLevel === 'HIGH_RISK' && (
                    <span className="phishing-badge high-risk" title="高危钓鱼邮件">
                      ⚠️
                    </span>
                  )}
                  {!isPending && displayLevel === 'SUSPICIOUS' && (
                    <span className="phishing-badge suspicious" title="疑似钓鱼邮件">
                      ⚡
                    </span>
                  )}
                </div>
                <div className="email-item-content">
                  {/* 第一行：主题 + 时间 */}
                  <div className="email-row email-row-subject">
                    <span className="email-subject">{email.subject || '(无主题)'}</span>
                    <span className="email-time">
                      {email.received_at ? new Date(email.received_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  {/* 第二行：内容摘要 */}
                  <div className="email-row email-row-snippet">
                    <span className="email-snippet">{email.snippet || ''}</span>
                    {isPending && <span className="phishing-pending-text">检测中</span>}
                  </div>
                  {/* 第三行：收件邮箱 */}
                  <div className="email-row email-row-recipient">
                    <span className="email-recipient">{email.email_address}</span>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </section>
  )
}