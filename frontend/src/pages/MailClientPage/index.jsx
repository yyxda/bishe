/**
 * 邮件客户端主页组件。
 *
 * 三栏布局：左侧邮箱列表、中间邮件列表、右侧邮件详情。
 */

import React, { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { useAccounts } from '../../hooks/useAccounts.js'
import { useEmails } from '../../hooks/useEmails.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import Sidebar from './Sidebar.jsx'
import EmailList from './EmailList.jsx'
import EmailDetail from './EmailDetail.jsx'
import { AddEmailModal, ComposeModal, WhitelistModal } from './Modals.jsx'
import '../MailClientPage.css'

/**
 * 邮件客户端主页。
 *
 * @returns {JSX.Element} 页面结构
 */
export default function MailClientPage() {
  const { user, token, logout } = useAuth()
  const accounts = useAccounts()
  const emails = useEmails()
  const { applyPhishingUpdate } = emails

  const [selectedAccountId, setSelectedAccountId] = useState(null)
  const [selectedFolder, setSelectedFolder] = useState('inbox')
  const [showAddEmailModal, setShowAddEmailModal] = useState(false)
  const [showComposeModal, setShowComposeModal] = useState(false)
  const [showWhitelistModal, setShowWhitelistModal] = useState(false)

  /**
   * 初始化加载邮箱账户和邮件。
   */
  useEffect(() => {
    const init = async () => {
      try {
        const accountList = await accounts.loadAccounts()
        if (accountList.length > 0) {
          // 学生登录后自动同步邮件
          if (user.role === 'user' || user.role === 'student') {
            await accounts.syncEmails(accountList[0].id)
          }
          await emails.loadEmails(null, 'inbox')
        }
      } catch (error) {
        Toast.error('加载数据失败，请刷新页面重试')
      }
    }
    init()
  }, [user])

  /**
   * 订阅钓鱼检测结果的SSE事件流。
   * 后台检测完成后推送增量更新，避免轮询刷新导致滚动位置丢失。
   */
  useEffect(() => {
    if (!token) return

    const baseUrl = '/api'
    const streamUrl = `${baseUrl}/phishing/stream?token=${encodeURIComponent(token)}`
    const eventSource = new EventSource(streamUrl)

    const handleUpdate = (event) => {
      try {
        const payload = JSON.parse(event.data)
        applyPhishingUpdate(payload)
      } catch (error) {
        console.debug('解析钓鱼检测事件失败:', error)
      }
    }

    eventSource.addEventListener('phishing_update', handleUpdate)

    eventSource.onerror = (error) => {
      console.debug('钓鱼检测事件流异常:', error)
    }

    return () => {
      eventSource.removeEventListener('phishing_update', handleUpdate)
      eventSource.close()
    }
  }, [token, applyPhishingUpdate])

  /**
   * 选择邮箱账户。
   */
  const handleSelectAccount = useCallback(
    async (accountId) => {
      setSelectedAccountId(accountId)
      setSelectedFolder('inbox')
      emails.clearSelection()
      try {
        await emails.loadEmails(accountId, 'inbox')
      } catch (error) {
        Toast.error('加载邮件失败')
      }
    },
    [emails]
  )

  /**
   * 选择文件夹。
   */
  const handleSelectFolder = useCallback(
    async (folder) => {
      setSelectedFolder(folder)
      emails.clearSelection()
      try {
        await emails.loadEmails(selectedAccountId, folder)
      } catch (error) {
        Toast.error('加载邮件失败')
      }
    },
    [emails, selectedAccountId]
  )

  /**
   * 选择邮件。
   */
  const handleSelectEmail = useCallback(
    async (email) => {
      await emails.selectEmail(email)
      // 标记已读
      if (!email.is_read) {
        try {
          await emails.markAsRead(email.id)
        } catch (error) {
          console.error('标记已读失败:', error)
        }
      }
    },
    [emails]
  )

  /**
   * 同步邮件。
   */
  const handleSyncEmails = useCallback(
    async (accountId) => {
      try {
        const result = await accounts.syncEmails(accountId)
        await emails.loadEmails(selectedAccountId, selectedFolder)
        if (result.synced_count > 0) {
          Toast.success(`同步成功，获取${result.synced_count}封新邮件`)
        } else {
          Toast.info('同步完成，暂无新邮件')
        }
      } catch (error) {
        Toast.error('同步邮件失败')
      }
    },
    [accounts, emails, selectedAccountId, selectedFolder]
  )

  /**
   * 添加邮箱账户。
   */
  const handleAddAccount = useCallback(
    async (formData) => {
      try {
        const result = await accounts.addAccount(formData)
        if (result.success) {
          setShowAddEmailModal(false)
          Toast.success('邮箱添加成功')
          // 自动同步
          if (result.account_id) {
            await handleSyncEmails(result.account_id)
          }
          return { success: true }
        }
        return { success: false, message: result.message }
      } catch (error) {
        return { success: false, message: error.message }
      }
    },
    [accounts, handleSyncEmails]
  )

  /**
   * 删除邮箱账户。
   */
  const handleDeleteAccount = useCallback(
    async (accountId, emailAddress) => {
      const confirmed = await ConfirmDialog.confirmDelete(emailAddress || '此邮箱账户')
      if (!confirmed) return

      try {
        await accounts.deleteAccount(accountId)
        Toast.success('邮箱账户已删除')

        // 如果删除的是当前选中的账户，切换到全部邮件视图
        if (selectedAccountId === accountId) {
          setSelectedAccountId(null)
        }

        // 清空当前选中的邮件和详情
        emails.clearSelection()

        // 重新加载邮件列表（使用更新后的选中状态）
        const newAccountId = selectedAccountId === accountId ? null : selectedAccountId
        await emails.loadEmails(newAccountId, selectedFolder)
      } catch (error) {
        Toast.error('删除邮箱失败')
      }
    },
    [accounts, emails, selectedAccountId, selectedFolder]
  )

  /**
   * 发送邮件。
   */
  const handleSendEmail = useCallback(
    async (formData) => {
      // 如果没有邮箱账户，自动使用登录的邮箱账户
      let accountId = null
      if (accounts.accounts.length === 0) {
        // 使用登录时的邮箱账户
        accountId = user.emailAccountId
      } else {
        accountId = accounts.accounts[0].id
      }

      if (!accountId) {
        return { success: false, message: '邮箱账户未配置，请重新登录' }
      }

      try {
        const result = await emails.sendEmail({
          email_account_id: accountId,
          ...formData,
        })
        if (result.success) {
          setShowComposeModal(false)
          Toast.success('邮件发送成功')
          return { success: true }
        }
        return { success: false, message: result.message }
      } catch (error) {
        return { success: false, message: error.message }
      }
    },
    [accounts.accounts, emails, user.emailAccountId]
  )

  /**
   * 登出处理。
   */
  const handleLogout = useCallback(() => {
    logout()
    Toast.info('已安全退出登录')
  }, [logout])

  /**
   * 重新检测邮件。
   */
  const handleRedetectEmails = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/emails/redetect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      if (data.success) {
        Toast.success(data.message)
      } else {
        Toast.error(data.message || '重新检测失败')
      }
    } catch (error) {
      Toast.error('重新检测失败: ' + error.message)
    }
  }, [])

  /**
   * 白名单管理。
   */
  const handleManageWhitelist = useCallback(() => {
    setShowWhitelistModal(true)
  }, [])

  return (
    <div className="mail-client">
      <Sidebar
        user={user}
        accounts={accounts.accounts}
        selectedAccountId={selectedAccountId}
        selectedFolder={selectedFolder}
        isLoading={accounts.isLoading}
        isSyncing={accounts.isSyncing}
        onSelectAccount={handleSelectAccount}
        onSelectFolder={handleSelectFolder}
        onSyncEmails={handleSyncEmails}
        onDeleteAccount={handleDeleteAccount}
        onAddEmail={user.role === 'admin' || user.role === 'super_admin' ? () => setShowAddEmailModal(true) : null}
        onCompose={() => setShowComposeModal(true)}
        onRedetectEmails={handleRedetectEmails}
        onManageWhitelist={handleManageWhitelist}
        onLogout={handleLogout}
      />

      {accounts.accounts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-content">
            <h3>还没有邮箱账户</h3>
            <p>{user.role === 'admin' || user.role === 'super_admin' ? '请添加邮箱账户以开始使用邮件功能' : '请重新登录以同步邮箱账户'}</p>
            {(user.role === 'admin' || user.role === 'super_admin') && (
              <button onClick={() => setShowAddEmailModal(true)}>添加邮箱账户</button>
            )}
          </div>
        </div>
      ) : (
        <EmailList
          emails={emails.emails}
          selectedEmail={emails.selectedEmail}
          isLoading={emails.isLoading}
          onSelectEmail={handleSelectEmail}
          folderName={selectedFolder === 'phishing' ? '钓鱼邮件' : '收件箱'}
        />
      )}

      <EmailDetail
        emailDetail={emails.emailDetail}
        isLoading={emails.isLoadingDetail}
        selectedEmail={emails.selectedEmail}
        user={user}
      />

      <AddEmailModal
        isOpen={showAddEmailModal}
        onClose={() => setShowAddEmailModal(false)}
        onSubmit={handleAddAccount}
      />

      <ComposeModal
        isOpen={showComposeModal}
        onClose={() => setShowComposeModal(false)}
        onSubmit={handleSendEmail}
        isSending={emails.isSending}
      />

      <WhitelistModal
        isOpen={showWhitelistModal}
        onClose={() => setShowWhitelistModal(false)}
      />
    </div>
  )
}