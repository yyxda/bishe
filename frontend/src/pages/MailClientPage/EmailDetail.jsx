/**
 * 邮件详情组件。
 *
 * 显示邮件内容，处理钓鱼邮件链接保护。
 */

import React, { useState, useCallback } from 'react'
import { formatConfidencePercent } from '../../utils/PhishingUtils.js'
import { useOverlayClose } from '../../hooks/useOverlayClose'

/**
 * 格式化收件人列表为友好显示。
 *
 * @param {Array|string} recipients 收件人列表或字符串
 * @returns {string} 格式化后的收件人字符串
 */
function formatRecipients(recipients) {
  if (!recipients) return ''
  
  // 如果是字符串，尝试解析JSON
  let recipientList = recipients
  if (typeof recipients === 'string') {
    try {
      recipientList = JSON.parse(recipients)
    } catch {
      return recipients // 如果解析失败，直接返回原字符串
    }
  }
  
  // 如果不是数组，直接返回字符串形式
  if (!Array.isArray(recipientList)) {
    return String(recipients)
  }
  
  // 只显示TO类型的收件人（过滤掉REPLY_TO、CC等）
  const toRecipients = recipientList.filter(r => r.type === 'TO')
  
  if (toRecipients.length === 0) {
    // 如果没有TO类型，显示所有收件人
    return recipientList
      .map(r => r.name ? `${r.name} <${r.address}>` : r.address)
      .join(', ')
  }
  
  return toRecipients
    .map(r => r.name ? `${r.name} <${r.address}>` : r.address)
    .join(', ')
}

/**
 * 邮件详情组件。
 *
 * @param {object} props 组件属性
 * @returns {JSX.Element} 邮件详情结构
 */
export default function EmailDetail({ emailDetail, isLoading, selectedEmail, user }) {
  if (!selectedEmail) {
    return (
      <section className="email-detail">
        <div className="empty-placeholder">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" strokeWidth="1">
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="M3 7l9 6 9-6" />
          </svg>
          <p>选择邮件查看详情</p>
        </div>
      </section>
    )
  }

  // Determine if full detail data is ready
  const isDataReady = !isLoading && emailDetail && emailDetail.id === selectedEmail.id;

  // Optimistic Data (Prefer detail, fallback to list data)
  const displaySubject = emailDetail?.subject || selectedEmail.subject || '(无主题)';
  const displaySender = emailDetail?.sender || selectedEmail.sender || '未知发件人';
  const displayDate = emailDetail?.received_at || selectedEmail.received_at;
  const displayPhishingLevel = emailDetail?.phishing_level || selectedEmail.phishing_level || 'NORMAL';
  const displayPhishingStatus = emailDetail?.phishing_status || selectedEmail.phishing_status || 'COMPLETED';
  const rawPhishingScore = emailDetail?.phishing_score ?? selectedEmail.phishing_score;
  const normalizedScore = Number(rawPhishingScore);
  const displayPhishingScore = Number.isFinite(normalizedScore) ? normalizedScore : 0;
  const normalizedPhishingLevel = (displayPhishingLevel || 'NORMAL').toUpperCase();
  const normalizedPhishingStatus = (displayPhishingStatus || 'COMPLETED').toUpperCase();
  const isDetectionPending = normalizedPhishingStatus !== 'COMPLETED';
  const confidenceText = formatConfidencePercent(displayPhishingScore);

  return (
    <section className="email-detail">
      <div className="detail-header">
        <div className={`phishing-warning ${isDetectionPending ? 'pending' : normalizedPhishingLevel?.toLowerCase()}`}>
          {isDetectionPending ? (
            <>
              <span className="warning-icon">⏳</span>
              <span>正在检测钓鱼邮件，请稍候...</span>
            </>
          ) : normalizedPhishingLevel === 'HIGH_RISK' ? (
            <>
              <span className="warning-icon">🚨</span>
              <span>高危钓鱼邮件 - 请勿点击任何链接</span>
            </>
          ) : normalizedPhishingLevel === 'SUSPICIOUS' ? (
            <>
              <span className="warning-icon">⚠️</span>
              <span>疑似钓鱼邮件 - 请谨慎对待</span>
            </>
          ) : (
            <>
              <span className="warning-icon">✅</span>
              <span>正常邮件 - 风险较低</span>
            </>
          )}
          {!isDetectionPending && (
            <span className="phishing-score">钓鱼邮件概率: {confidenceText}</span>
          )}
        </div>
        
        <h1 className="detail-subject">{displaySubject}</h1>
        
        <div className="detail-meta">
          <div className="detail-from">
            <span className="label">发件人:</span>
            <span className="value">{displaySender}</span>
          </div>
          <div className="detail-to">
            <span className="label">收件人:</span>
            <span className="value">
                {isDataReady 
                    ? formatRecipients(emailDetail.recipients) 
                    : <div className="skeleton skeleton-line short" style={{display: 'inline-block', width: '200px', verticalAlign: 'middle', margin: 0}} />}
            </span>
          </div>
          <div className="detail-time">
            <span className="label">时间:</span>
            <span className="value">
              {displayDate ? new Date(displayDate).toLocaleString() : ''}
            </span>
          </div>
        </div>
      </div>

      <div className="detail-body">
        {isDataReady ? (
            <PhishingProtectedContent
              content={emailDetail.content_html || emailDetail.content_text}
              phishingLevel={isDetectionPending ? 'NORMAL' : normalizedPhishingLevel}
              isHtml={!!emailDetail.content_html}
              userStudentId={user?.studentId}
            />
        ) : (
            <div className="loading-placeholder">
                <div className="spinner spin" style={{
                    width: '32px', 
                    height: '32px', 
                    border: '3px solid rgba(31, 138, 112, 0.1)', 
                    borderTopColor: 'var(--color-primary)', 
                    borderRadius: '50%',
                    marginBottom: '16px'
                }}></div>
                <div className="skeleton skeleton-line medium" />
                <div className="skeleton skeleton-line full" />
                <div className="skeleton skeleton-line full" />
            </div>
        )}
      </div>
    </section>
  )
}

/**
 * 钓鱼保护内容组件。
 *
 * 根据钓鱼等级处理邮件内容中的链接。
 */
function PhishingProtectedContent({ content, phishingLevel, isHtml, userStudentId }) {
  const [showLinkModal, setShowLinkModal] = useState(false)
  const [pendingLink, setPendingLink] = useState('')
  const [studentIdInput, setStudentIdInput] = useState('')
  const [verifyError, setVerifyError] = useState('')
  
  // 使用 hook 处理遮罩层关闭逻辑
  const closeLinkModal = useCallback(() => setShowLinkModal(false), [])
  const { handleMouseDown, handleClick } = useOverlayClose(closeLinkModal)

  /**
   * 处理高危链接点击。
   */
  const handleHighRiskLinkClick = useCallback((url) => {
    setPendingLink(url)
    setStudentIdInput('')
    setVerifyError('')
    setShowLinkModal(true)
  }, [])

  /**
   * 验证学号并复制链接。
   */
  const handleVerifyAndCopy = useCallback(() => {
    if (!studentIdInput.trim()) {
      setVerifyError('请输入您的学号。')
      return
    }

    // 验证输入的学号是否与当前用户学号匹配
    if (studentIdInput.trim() !== userStudentId) {
      setVerifyError('学号验证失败，请输入正确的学号。')
      return
    }

    navigator.clipboard
      .writeText(pendingLink)
      .then(() => {
        setShowLinkModal(false)
        alert('链接已复制到剪贴板。请自行判断是否访问，注意安全！')
      })
      .catch(() => {
        setVerifyError('复制失败，请手动复制。')
      })
  }, [studentIdInput, userStudentId, pendingLink])

  /**
   * 从纯文本中提取URL。
   */
  const extractTextUrls = useCallback((text) => {
    if (!text) return []
    // 匹配http/https开头的URL
    const urlRegex = /https?:\/\/[^\s<>"'\(\)\[\]{}]+/gi
    const matches = text.match(urlRegex)
    return matches || []
  }, [])

  /**
   * 渲染内容。
   */
  const renderContent = () => {
    if (!content) {
      return <p className="no-content">（无内容）</p>
    }

    // 正常邮件直接显示
    if (phishingLevel === 'NORMAL') {
      if (isHtml) {
        return <div className="email-html-content" dangerouslySetInnerHTML={{ __html: content }} />
      }
      return <pre className="email-text-content">{content}</pre>
    }

    // 疑似钓鱼：将链接变为纯文本
    if (phishingLevel === 'SUSPICIOUS') {
      let processedContent = content
      if (isHtml) {
        processedContent = content.replace(
          /<a\s+[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi,
          '<span class="disabled-link" title="链接已禁用: $1">$2 [链接已禁用]</span>'
        )
        return (
          <div
            className="email-html-content suspicious"
            dangerouslySetInnerHTML={{ __html: processedContent }}
          />
        )
      }
      // 纯文本：标记链接但不隐藏
      const textUrls = extractTextUrls(content)
      if (textUrls.length > 0) {
        let processedText = content
        textUrls.forEach((url) => {
          processedText = processedText.replace(url, `[链接已禁用: ${url.substring(0, 50)}...]`)
        })
        return <pre className="email-text-content suspicious">{processedText}</pre>
      }
      return <pre className="email-text-content">{content}</pre>
    }

    // 高危钓鱼：隐藏链接，添加查看按钮
    if (phishingLevel === 'HIGH_RISK') {
      if (isHtml) {
        const linkRegex = /<a\s+[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi
        const links = []
        let match
        const contentCopy = content
        while ((match = linkRegex.exec(contentCopy)) !== null) {
          links.push({ url: match[1], text: match[2] })
        }

        const processedContent = content.replace(linkRegex, '<span class="hidden-link">[链接已隐藏]</span>')

        return (
          <div className="high-risk-content">
            <div
              className="email-html-content high-risk"
              dangerouslySetInnerHTML={{ __html: processedContent }}
            />
            {links.length > 0 && (
              <div className="hidden-links-section">
                <p className="warning-text">检测到 {links.length} 个可疑链接：</p>
                {links.map((link, index) => (
                  <button
                    key={index}
                    className="btn-view-link"
                    onClick={() => handleHighRiskLinkClick(link.url)}
                  >
                    点击查看疑似钓鱼链接 #{index + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        )
      }

      // 纯文本高危：隐藏URL，显示查看按钮
      const textUrls = extractTextUrls(content)
      if (textUrls.length > 0) {
        let processedText = content
        // 将所有URL替换为占位符
        textUrls.forEach((url) => {
          processedText = processedText.replace(url, '[链接已隐藏]')
        })

        return (
          <div className="high-risk-content">
            <pre className="email-text-content high-risk">{processedText}</pre>
            <div className="hidden-links-section">
              <p className="warning-text">检测到 {textUrls.length} 个可疑链接：</p>
              {textUrls.map((url, index) => (
                <button
                  key={index}
                  className="btn-view-link"
                  onClick={() => handleHighRiskLinkClick(url)}
                >
                  点击查看疑似钓鱼链接 #{index + 1}
                </button>
              ))}
            </div>
          </div>
        )
      }

      return <pre className="email-text-content">{content}</pre>
    }

    return <pre className="email-text-content">{content}</pre>
  }

  return (
    <>
      {renderContent()}

      {showLinkModal && (
        <div className="modal-overlay" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header warning">
              <h3>⚠️ 高危链接警告</h3>
              <button className="btn-close" onClick={() => setShowLinkModal(false)}>
                ×
              </button>
            </div>

            <div className="modal-body">
              <p className="warning-text">这是一个疑似钓鱼链接，请谨慎操作！</p>
              <div className="link-display">
                <code>{pendingLink}</code>
              </div>
              <p>为确认您已了解风险，请输入您的学号：</p>
              <input
                type="text"
                placeholder="请输入您的学号"
                value={studentIdInput}
                onChange={(e) => setStudentIdInput(e.target.value)}
                className="school-input"
              />
              {verifyError && <div className="form-error">{verifyError}</div>}
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowLinkModal(false)}>
                取消
              </button>
              <button className="btn-warning" onClick={handleVerifyAndCopy}>
                确认复制链接
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}