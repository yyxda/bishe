/**
 * 钓鱼检测服务。
 */

import ApiClient from './ApiClient.js'

class PhishingService {
  constructor() {
    const baseUrl = '/api'
    this.client = new ApiClient(baseUrl)
  }

  /**
   * 验证学号并获取链接。
   *
   * @param {string} studentId 学号
   * @param {string} linkUrl 链接地址
   * @returns {Promise<object>} 验证结果
   */
  async verifyLink(studentId, linkUrl) {
    return this.client.post('/verify-link', {
      student_id: studentId,
      link_url: linkUrl,
    })
  }

  /**
   * 获取钓鱼检测统计。
   *
   * @returns {Promise<object>} 统计数据
   */
  async getStats() {
    return this.client.get('/stats')
  }
}

export default new PhishingService()