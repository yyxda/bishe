/**
 * 邮箱账户管理Hook。
 *
 * 提供邮箱账户的增删查改和同步功能。
 */

import { useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext.jsx'
import EmailAccountService from '../services/EmailAccountService.js'

/**
 * 邮箱账户管理Hook。
 *
 * @returns {object} 邮箱账户状态和操作方法
 */
export function useAccounts() {
  const { token } = useAuth()
  const [accounts, setAccounts] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState(null)

  /**
   * 获取API服务实例。
   */
  const getService = useCallback(() => {
    return EmailAccountService.createWithToken(token)
  }, [token])

  /**
   * 加载邮箱账户列表。
   */
  const loadAccounts = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getService().getAccounts()
      setAccounts(data)
      return data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [getService])

  /**
   * 添加邮箱账户。
   *
   * @param {object} accountData 账户数据
   * @returns {Promise<object>} 添加结果
   */
  const addAccount = useCallback(
    async (accountData) => {
      setError(null)
      try {
        const result = await getService().addAccount(accountData)
        if (result.success) {
          await loadAccounts()
        }
        return result
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    [getService, loadAccounts]
  )

  /**
   * 删除邮箱账户。
   *
   * @param {number} accountId 账户ID
   * @returns {Promise<void>}
   */
  const deleteAccount = useCallback(
    async (accountId) => {
      setError(null)
      try {
        await getService().deleteAccount(accountId)
        await loadAccounts()
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    [getService, loadAccounts]
  )

  /**
   * 同步邮箱邮件。
   *
   * @param {number} accountId 账户ID
   * @returns {Promise<object>} 同步结果
   */
  const syncEmails = useCallback(
    async (accountId) => {
      setIsSyncing(true)
      setError(null)
      try {
        const result = await getService().syncEmails(accountId)
        return result
      } catch (err) {
        setError(err.message)
        throw err
      } finally {
        setIsSyncing(false)
      }
    },
    [getService]
  )

  /**
   * 测试邮箱连接。
   *
   * @param {object} connectionData 连接数据
   * @returns {Promise<object>} 测试结果
   */
  const testConnection = useCallback(
    async (connectionData) => {
      setError(null)
      try {
        return await getService().testConnection(connectionData)
      } catch (err) {
        setError(err.message)
        throw err
      }
    },
    [getService]
  )

  return {
    accounts,
    isLoading,
    isSyncing,
    error,
    loadAccounts,
    addAccount,
    deleteAccount,
    syncEmails,
    testConnection,
  }
}

export default useAccounts
