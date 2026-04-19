import ApiClient from './ApiClient.js'

/**
 * 邮箱账户服务类。
 *
 * 提供邮箱账户管理相关的API调用。
 */
export default class EmailAccountService {
  /**
   * @param {ApiClient} apiClient API客户端
   */
  constructor(apiClient) {
    this.apiClient = apiClient
  }

  /**
   * 创建默认服务实例。
   * @returns {EmailAccountService} 服务实例
   */
  static createDefault() {
    return new EmailAccountService(new ApiClient('/api'))
  }

  /**
   * 使用指定令牌创建服务实例。
   * @param {string} token JWT访问令牌
   * @returns {EmailAccountService} 服务实例
   */
  static createWithToken(token) {
    return new EmailAccountService(new ApiClient('/api', token))
  }

  /**
   * 获取邮箱账户列表。
   * @returns {Promise<Array>} 邮箱账户列表
   */
  async getAccounts() {
    const response = await this.apiClient.get('/email-accounts')
    if (response?.success) {
      return response.accounts || []
    }
    return []
  }

  /**
   * 添加邮箱账户。
   * @param {object} data 邮箱账户数据
   * @returns {Promise<object>} 添加结果
   */
  async addAccount(data) {
    return await this.apiClient.post('/email-accounts', data)
  }

  /**
   * 删除邮箱账户。
   * @param {number} accountId 邮箱账户ID
   * @returns {Promise<object>} 删除结果
   */
  async deleteAccount(accountId) {
    return await this.apiClient.delete(`/email-accounts/${accountId}`)
  }

  /**
   * 同步邮箱邮件。
   * @param {number} accountId 邮箱账户ID
   * @returns {Promise<object>} 同步结果
   */
  async syncEmails(accountId) {
    return await this.apiClient.post(`/email-accounts/${accountId}/sync`, {})
  }

  /**
   * 测试邮箱连接。
   * @param {object} data 测试连接数据
   * @returns {Promise<object>} 测试结果
   */
  async testConnection(data) {
    return await this.apiClient.post('/email-accounts/test-connection', data)
  }
}