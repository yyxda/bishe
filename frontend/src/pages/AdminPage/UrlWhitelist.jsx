/**
 * URL白名单管理组件。
 *
 * 提供URL规则的添加、编辑、删除功能。
 * 支持Clash风格的域名规则（DOMAIN、DOMAIN-SUFFIX、DOMAIN-KEYWORD）。
 */

import React, { useState, useEffect, useCallback } from 'react'
import AdminService from '../../services/AdminService.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { useOverlayClose } from '../../hooks/useOverlayClose'

const adminService = new AdminService()

const RULE_TYPES = [
  { value: 'DOMAIN', label: 'DOMAIN', desc: '精确匹配域名' },
  { value: 'DOMAIN-SUFFIX', label: 'DOMAIN-SUFFIX', desc: '匹配域名后缀' },
  { value: 'DOMAIN-KEYWORD', label: 'DOMAIN-KEYWORD', desc: '匹配域名关键词' },
]

/**
 * URL白名单管理组件。
 *
 * @returns {JSX.Element} 白名单管理界面
 */
export default function UrlWhitelist() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [formData, setFormData] = useState({
    ruleType: 'DOMAIN',
    ruleValue: '',
    description: '',
  })
  const [submitting, setSubmitting] = useState(false)
  
  // 使用 hook 处理遮罩层关闭逻辑
  const closeAddModal = useCallback(() => setShowAddModal(false), [])
  const { handleMouseDown, handleClick } = useOverlayClose(closeAddModal)

  /**
   * 加载规则列表。
   */
  const loadRules = useCallback(async () => {
    setLoading(true)
    try {
      const response = await adminService.getWhitelistRules()
      setRules(response.rules || [])
    } catch (error) {
      Toast.error('加载规则列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRules()
  }, [loadRules])

  /**
   * 打开添加模态框。
   */
  const handleOpenAdd = () => {
    setFormData({ ruleType: 'DOMAIN', ruleValue: '', description: '' })
    setEditingRule(null)
    setShowAddModal(true)
  }

  /**
   * 打开编辑模态框。
   */
  const handleOpenEdit = (rule) => {
    setFormData({
      ruleType: rule.rule_type,
      ruleValue: rule.rule_value,
      description: rule.description || '',
    })
    setEditingRule(rule)
    setShowAddModal(true)
  }

  /**
   * 处理表单提交。
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return

    if (!formData.ruleValue.trim()) {
      Toast.error('请输入规则值')
      return
    }

    setSubmitting(true)
    try {
      if (editingRule) {
        await adminService.updateWhitelistRule(editingRule.id, {
          rule_type: formData.ruleType,
          rule_value: formData.ruleValue,
          description: formData.description,
        })
        Toast.success('规则更新成功')
      } else {
        await adminService.createWhitelistRule(
          formData.ruleType,
          formData.ruleValue,
          formData.description
        )
        Toast.success('规则添加成功')
      }
      setShowAddModal(false)
      loadRules()
    } catch (error) {
      Toast.error((editingRule ? '更新' : '添加') + '规则失败: ' + error.message)
    } finally {
      setSubmitting(false)
    }
  }

  /**
   * 删除规则。
   */
  const handleDeleteRule = async (rule) => {
    const confirmed = await ConfirmDialog.show({
      title: '删除规则',
      message: `确定要删除规则 "${rule.rule_type}:${rule.rule_value}" 吗？`,
      confirmText: '删除',
      type: 'danger',
    })

    if (!confirmed) return

    try {
      await adminService.deleteWhitelistRule(rule.id)
      Toast.success('规则已删除')
      loadRules()
    } catch (error) {
      Toast.error('删除规则失败: ' + error.message)
    }
  }

  /**
   * 获取规则类型样式类。
   */
  const getRuleTypeClass = (type) => {
    switch (type) {
      case 'DOMAIN':
        return 'domain'
      case 'DOMAIN-SUFFIX':
        return 'domain-suffix'
      case 'DOMAIN-KEYWORD':
        return 'domain-keyword'
      default:
        return ''
    }
  }

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>URL白名单规则 ({rules.length})</h2>
        <button className="btn-add" onClick={handleOpenAdd}>
          + 添加规则
        </button>
      </div>

      <div style={{ marginBottom: '16px', padding: '12px 16px', background: 'var(--color-primary-lighter)', borderRadius: '10px', fontSize: '0.9rem' }}>
        <strong>💡 规则说明：</strong>
        <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
          <li><code>DOMAIN</code>：精确匹配，如 <code>mail.qq.com</code></li>
          <li><code>DOMAIN-SUFFIX</code>：后缀匹配，如 <code>qq.com</code> 可匹配 <code>mail.qq.com</code></li>
          <li><code>DOMAIN-KEYWORD</code>：关键词匹配，如 <code>192.168</code> 可匹配所有内网地址</li>
        </ul>
        <p style={{ margin: '8px 0 0', color: 'var(--color-ink-secondary)' }}>
          注意：规则仅匹配URL的域名部分，不匹配路径和查询参数。
        </p>
      </div>

      {loading ? (
        <div className="empty-state">
          <p>加载中...</p>
        </div>
      ) : rules.length === 0 ? (
        <div className="empty-state">
          <p>暂无白名单规则</p>
        </div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>规则类型</th>
              <th>规则值</th>
              <th>描述</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id}>
                <td>
                  <span className={`rule-type-badge ${getRuleTypeClass(rule.rule_type)}`}>
                    {rule.rule_type}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{rule.rule_value}</td>
                <td>{rule.description || '-'}</td>
                <td>
                  <span className={`status-badge ${rule.is_active ? 'active' : 'inactive'}`}>
                    {rule.is_active ? '✓ 启用' : '✗ 停用'}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <button
                      className="btn-action primary"
                      onClick={() => handleOpenEdit(rule)}
                    >
                      编辑
                    </button>
                    <button
                      className="btn-action danger"
                      onClick={() => handleDeleteRule(rule)}
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* 添加/编辑规则模态框 */}
      {showAddModal && (
        <div className="modal-overlay admin-modal" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRule ? '编辑规则' : '添加规则'}</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <form className="admin-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>规则类型</label>
                  <select
                    value={formData.ruleType}
                    onChange={(e) =>
                      setFormData({ ...formData, ruleType: e.target.value })
                    }
                  >
                    {RULE_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label} - {type.desc}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>规则值</label>
                  <input
                    type="text"
                    placeholder={
                      formData.ruleType === 'DOMAIN'
                        ? '如：mail.qq.com'
                        : formData.ruleType === 'DOMAIN-SUFFIX'
                        ? '如：qq.com'
                        : '如：192.168'
                    }
                    value={formData.ruleValue}
                    onChange={(e) =>
                      setFormData({ ...formData, ruleValue: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>描述（可选）</label>
                  <input
                    type="text"
                    placeholder="规则描述"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                  />
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-cancel"
                    onClick={() => setShowAddModal(false)}
                  >
                    取消
                  </button>
                  <button type="submit" className="btn-submit" disabled={submitting}>
                    {submitting ? '保存中...' : editingRule ? '更新' : '添加'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
