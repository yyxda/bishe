/**
 * API 请求客户端。
 *
 * 支持JWT Bearer令牌认证。
 */
export default class ApiClient {
  /**
   * @param {string} baseUrl API 基础地址
   * @param {string|null} token JWT访问令牌
   */
  constructor(baseUrl, token = null) {
    this.baseUrl = (baseUrl || '').replace(/\/$/, '')
    this.token = token
  }

  /**
   * 获取令牌（从构造函数参数或localStorage）。
   * @returns {string|null} JWT令牌
   */
  _getToken() {
    return this.token || localStorage.getItem('token')
  }

  /**
   * 构建请求头。
   * @returns {object} 请求头对象
   */
  _buildHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    }

    const token = this._getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }

  /**
   * 发送 GET 请求。
   * @param {string} path 请求路径
   * @returns {Promise<object>} 响应数据
   */

  async get(path) {
    const response = await fetch(this._buildUrl(path), {
      method: 'GET',
      headers: this._buildHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        throw new Error('会话已过期，请重新登录')
      }
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 POST 请求。
   * @param {string} path 请求路径
   * @param {object} body 请求体
   * @returns {Promise<object>} 响应数据
   */
  async post(path, body) {
    const response = await fetch(this._buildUrl(path), {
      method: 'POST',
      headers: this._buildHeaders(),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        throw new Error('会话已过期，请重新登录')
      }
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 DELETE 请求。
   * @param {string} path 请求路径
   * @returns {Promise<object>} 响应数据
   */
  async delete(path) {
    const response = await fetch(this._buildUrl(path), {
      method: 'DELETE',
      headers: this._buildHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        throw new Error('会话已过期，请重新登录')
      }
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 PATCH 请求。
   * @param {string} path 请求路径
   * @param {object} body 请求体
   * @returns {Promise<object>} 响应数据
   */
  async patch(path, body) {
    const response = await fetch(this._buildUrl(path), {
      method: 'PATCH',
      headers: this._buildHeaders(),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        throw new Error('会话已过期，请重新登录')
      }
      const errorData = await this._safeJson(response)
      const message = errorData?.message || errorData?.detail || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 PUT 请求。
   * @param {string} path 请求路径
   * @param {object} body 请求体
   * @returns {Promise<object>} 响应数据
   */
  async put(path, body) {
    const response = await fetch(this._buildUrl(path), {
      method: 'PUT',
      headers: this._buildHeaders(),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        throw new Error('会话已过期，请重新登录')
      }
      const errorData = await this._safeJson(response)
      const message = errorData?.message || errorData?.detail || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 构建完整请求地址。
   * @param {string} path 请求路径
   * @returns {string} 完整 URL
   */
  _buildUrl(path) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    return `${this.baseUrl}${normalizedPath}`
  }

  /**
   * 安全解析 JSON，避免空响应导致异常。
   * @param {Response} response Fetch 响应对象
   * @returns {Promise<object | null>} 解析结果
   */
  async _safeJson(response) {
    try {
      return await response.json()
    } catch (error) {
      return null
    }
  }
}
