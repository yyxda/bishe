/**
 * 管理员API服务。
 *
 * 提供学生管理、管理员管理和URL白名单管理功能。
 */
import ApiClient from './ApiClient.js'

const API_BASE = '/api'

export default class AdminService {
  constructor() {
    this.client = new ApiClient(API_BASE)
  }

  // ========== 学生管理 ==========

  /**
   * 获取学生列表。
   * @param {number} page 页码
   * @param {number} pageSize 每页数量
   * @returns {Promise<object>} 学生列表响应
   */
  async getStudents(page = 1, pageSize = 20) {
    return this.client.get(`/admin/students?page=${page}&page_size=${pageSize}`)
  }

  /**
   * 创建学生。
   * @param {string} studentId 学号
   * @param {string} password 密码
   * @param {string} displayName 显示名称
   * @returns {Promise<object>} 创建结果
   */
  async createStudent(studentId, password, displayName) {
    return this.client.post('/admin/students', {
      student_id: studentId,
      password: password,
      display_name: displayName,
    })
  }

  /**
   * 设置学生状态。
   * @param {number} userId 用户ID
   * @param {boolean} isActive 是否启用
   * @returns {Promise<object>} 操作结果
   */
  async setStudentStatus(userId, isActive) {
    return this.client.patch(`/admin/students/${userId}/status`, {
      is_active: isActive,
    })
  }

  /**
   * 删除学生。
   * @param {number} userId 用户ID
   * @returns {Promise<object>} 操作结果
   */
  async deleteStudent(userId) {
    return this.client.delete(`/admin/students/${userId}`)
  }

  // ========== 管理员管理（仅超级管理员） ==========

  /**
   * 获取管理员列表。
   * @param {number} page 页码
   * @param {number} pageSize 每页数量
   * @returns {Promise<object>} 管理员列表响应
   */
  async getAdmins(page = 1, pageSize = 20) {
    return this.client.get(`/admin/admins?page=${page}&page_size=${pageSize}`)
  }

  /**
   * 创建管理员。
   * @param {string} studentId 账号
   * @param {string} password 密码
   * @param {string} displayName 显示名称
   * @returns {Promise<object>} 创建结果
   */
  async createAdmin(studentId, password, displayName) {
    return this.client.post('/admin/admins', {
      student_id: studentId,
      password: password,
      display_name: displayName,
    })
  }

  /**
   * 设置管理员状态。
   * @param {number} userId 用户ID
   * @param {boolean} isActive 是否启用
   * @returns {Promise<object>} 操作结果
   */
  async setAdminStatus(userId, isActive) {
    return this.client.patch(`/admin/admins/${userId}/status`, {
      is_active: isActive,
    })
  }

  /**
   * 删除管理员。
   * @param {number} userId 用户ID
   * @returns {Promise<object>} 操作结果
   */
  async deleteAdmin(userId) {
    return this.client.delete(`/admin/admins/${userId}`)
  }

  // ========== 旧接口兼容 ==========

  /**
   * 获取用户列表（兼容旧接口）。
   * @param {number} page 页码
   * @param {number} pageSize 每页数量
   * @returns {Promise<object>} 用户列表响应
   */
  async getUsers(page = 1, pageSize = 20) {
    return this.client.get(`/admin/users?page=${page}&page_size=${pageSize}`)
  }

  // ========== 白名单管理 ==========

  /**
   * 获取白名单规则列表。
   * @returns {Promise<object>} 规则列表响应
   */
  async getWhitelistRules() {
    return this.client.get('/admin/whitelist')
  }

  /**
   * 创建白名单规则。
   * @param {string} ruleType 规则类型
   * @param {string} ruleValue 规则值
   * @param {string} description 描述
   * @returns {Promise<object>} 创建结果
   */
  async createWhitelistRule(ruleType, ruleValue, description = '') {
    return this.client.post('/admin/whitelist', {
      rule_type: ruleType,
      rule_value: ruleValue,
      description: description,
    })
  }

  /**
   * 更新白名单规则。
   * @param {number} ruleId 规则ID
   * @param {object} data 更新数据
   * @returns {Promise<object>} 更新结果
   */
  async updateWhitelistRule(ruleId, data) {
    return this.client.put(`/admin/whitelist/${ruleId}`, data)
  }

  /**
   * 删除白名单规则。
   * @param {number} ruleId 规则ID
   * @returns {Promise<object>} 操作结果
   */
  async deleteWhitelistRule(ruleId) {
    return this.client.delete(`/admin/whitelist/${ruleId}`)
  }

  // ========== 发件人白名单管理 ==========

  /**
   * 获取发件人白名单规则列表。
   * @returns {Promise<object>} 规则列表响应
   */
  async getSenderWhitelistRules() {
    return this.client.get('/admin/sender-whitelist')
  }

  /**
   * 创建发件人白名单规则。
   * @param {string} ruleType 规则类型
   * @param {string} ruleValue 规则值
   * @param {string} description 描述
   * @returns {Promise<object>} 创建结果
   */
  async createSenderWhitelistRule(ruleType, ruleValue, description = '') {
    return this.client.post('/admin/sender-whitelist', {
      rule_type: ruleType,
      rule_value: ruleValue,
      description: description,
    })
  }

  /**
   * 更新发件人白名单规则。
   * @param {number} ruleId 规则ID
   * @param {object} data 更新数据
   * @returns {Promise<object>} 更新结果
   */
  async updateSenderWhitelistRule(ruleId, data) {
    return this.client.put(`/admin/sender-whitelist/${ruleId}`, data)
  }

  /**
   * 删除发件人白名单规则。
   * @param {number} ruleId 规则ID
   * @returns {Promise<object>} 操作结果
   */
  async deleteSenderWhitelistRule(ruleId) {
    return this.client.delete(`/admin/sender-whitelist/${ruleId}`)
  }
}