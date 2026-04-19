import ApiClient from './ApiClient.js'
import { LoginRequest, LoginResponse } from '../models/LoginModels.js'

/**
 * 认证服务类。
 */
export default class AuthService {
  /**
   * @param {ApiClient} apiClient API 客户端
   */
  constructor(apiClient) {
    this.apiClient = apiClient
  }

  /**
   * 创建默认服务实例。
   * @returns {AuthService} 认证服务
   */
  static createDefault() {
    const baseUrl = '/api'
    return new AuthService(new ApiClient(baseUrl))
  }

  /**
   * 发起登录请求。
   * @param {string} studentId 学号
   * @param {string} password 密码
   * @returns {Promise<LoginResponse>} 登录响应
   */
  async login(studentId, password, emailType = 'qq', authCode = '') {
    const request = new LoginRequest(studentId, password, emailType, authCode)
    const response = await this.apiClient.post('/auth/login', request.toJson())
    return LoginResponse.fromJson(response)
  }
}