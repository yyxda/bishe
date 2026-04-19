/**
 * 邮件管理Hook。
 *
 * 提供邮件列表获取、详情查看、发送和标记已读功能。
 */

import { useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext.jsx'
import EmailService from '../services/EmailService.js'

/**
 * 邮件管理Hook。
 *
 * @returns {object} 邮件状态和操作方法
 */
export function useEmails() {
  const { token } = useAuth()
  const [emails, setEmails] = useState([])
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [emailDetail, setEmailDetail] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState(null)

  /**
   * 获取API服务实例。
   */
  const getService = useCallback(() => {
    return EmailService.createWithToken(token)
  }, [token])

  /**
   * 加载邮件列表。
   *
   * @param {number|null} accountId 账户ID，null表示全部
   * @param {string|null} folder 文件夹类型：inbox(收件箱), phishing(钓鱼邮件)
   * @returns {Promise<Array>} 邮件列表
   */
  const loadEmails = useCallback(
    async (accountId = null, folder = null) => {
      setIsLoading(true)
      setError(null)
      try {
        // 使用默认limit=50, offset=0获取邮件
        const data = await getService().getEmails(accountId, folder)
        setEmails(data)
        return data
      } catch (err) {
        setError(err.message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [getService]
  )

  /**
   * 加载邮件详情。
   *
   * @param {number} emailId 邮件ID
   * @returns {Promise<object>} 邮件详情
   */
  const loadEmailDetail = useCallback(
    async (emailId) => {
      setIsLoadingDetail(true)
      setError(null)
      try {
        const detail = await getService().getEmailDetail(emailId)
        setEmailDetail(detail)
        return detail
      } catch (err) {
        setError(err.message)
        throw err
      } finally {
        setIsLoadingDetail(false)
      }
    },
    [getService]
  )

  /**
   * 选择邮件并加载详情。
   *
   * @param {object} email 邮件对象
   */
  const selectEmail = useCallback(
    async (email) => {
      setSelectedEmail(email)
      if (email) {
        await loadEmailDetail(email.id)
      } else {
        setEmailDetail(null)
      }
    },
    [loadEmailDetail]
  )

  /**
   * 发送邮件。
   *
   * @param {object} emailData 邮件数据
   * @returns {Promise<object>} 发送结果
   */
  const sendEmail = useCallback(
    async (emailData) => {
      setIsSending(true)
      setError(null)
      try {
        const result = await getService().sendEmail(emailData)
        return result
      } catch (err) {
        setError(err.message)
        throw err
      } finally {
        setIsSending(false)
      }
    },
    [getService]
  )

  /**
   * 标记邮件为已读。
   *
   * @param {number} emailId 邮件ID
   * @returns {Promise<void>}
   */
  const markAsRead = useCallback(
    async (emailId) => {
      setError(null)
      try {
        await getService().markAsRead(emailId)
        // 更新本地状态
        setEmails((prev) =>
          prev.map((e) => (e.id === emailId ? { ...e, is_read: true } : e))
        )
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    [getService]
  )

  /**
   * 清除选中状态。
   */
  const clearSelection = useCallback(() => {
    setSelectedEmail(null)
    setEmailDetail(null)
  }, [])

  /**
   * 应用钓鱼检测结果的增量更新。
   *
   * @param {object} update 检测更新数据
   */
  const applyPhishingUpdate = useCallback((update) => {
    if (!update || !update.email_id) {
      return
    }

    setEmails((prev) =>
      prev.map((email) =>
        email.id === update.email_id
          ? {
              ...email,
              phishing_level: update.phishing_level ?? email.phishing_level,
              phishing_score: update.phishing_score ?? email.phishing_score,
              phishing_status: update.phishing_status ?? email.phishing_status,
              phishing_reason: update.phishing_reason ?? email.phishing_reason,
            }
          : email
      )
    )

    setSelectedEmail((prev) =>
      prev?.id === update.email_id
        ? {
            ...prev,
            phishing_level: update.phishing_level ?? prev.phishing_level,
            phishing_score: update.phishing_score ?? prev.phishing_score,
            phishing_status: update.phishing_status ?? prev.phishing_status,
            phishing_reason: update.phishing_reason ?? prev.phishing_reason,
          }
        : prev
    )

    setEmailDetail((prev) =>
      prev?.id === update.email_id
        ? {
            ...prev,
            phishing_level: update.phishing_level ?? prev.phishing_level,
            phishing_score: update.phishing_score ?? prev.phishing_score,
            phishing_status: update.phishing_status ?? prev.phishing_status,
            phishing_reason: update.phishing_reason ?? prev.phishing_reason,
          }
        : prev
    )
  }, [])

  return {
    emails,
    selectedEmail,
    emailDetail,
    isLoading,
    isLoadingDetail,
    isSending,
    error,
    loadEmails,
    loadEmailDetail,
    selectEmail,
    sendEmail,
    markAsRead,
    clearSelection,
    applyPhishingUpdate,
  }
}

export default useEmails