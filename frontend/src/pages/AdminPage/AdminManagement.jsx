/**
 * 管理员管理组件（仅超级管理员可见）。
 *
 * 提供管理员的添加、删除、停用功能。
 */

import React, { useState, useEffect, useCallback } from 'react'
import AdminService from '../../services/AdminService.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { useOverlayClose } from '../../hooks/useOverlayClose'

const adminService = new AdminService()

/**
 * 管理员管理组件。
 *
 * @returns {JSX.Element} 管理员管理界面
 */
export default function AdminManagement() {
  const [admins, setAdmins] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [formData, setFormData] = useState({
    studentId: '',
    password: '',
    displayName: '',
  })
  const [submitting, setSubmitting] = useState(false)
  
  // 使用 hook 处理遮罩层关闭逻辑
  const closeAddModal = useCallback(() => setShowAddModal(false), [])
  const { handleMouseDown, handleClick } = useOverlayClose(closeAddModal)

  const pageSize = 20

  /**
   * 加载管理员列表。
   */
  const loadAdmins = useCallback(async () => {
    setLoading(true)
    try {
      const response = await adminService.getAdmins(page, pageSize)
      setAdmins(response.users || [])
      setTotal(response.total || 0)
    } catch (error) {
      Toast.error('加载管理员列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    loadAdmins()
  }, [loadAdmins])

  /**
   * 处理添加管理员表单提交。
   */
  const handleAddAdmin = async (e) => {
    e.preventDefault()
    if (submitting) return

    if (!formData.studentId || !formData.password || !formData.displayName) {
      Toast.error('请填写完整信息')
      return
    }

    setSubmitting(true)
    try {
      await adminService.createAdmin(
        formData.studentId,
        formData.password,
        formData.displayName
      )
      Toast.success('管理员添加成功')
      setShowAddModal(false)
      setFormData({ studentId: '', password: '', displayName: '' })
      loadAdmins()
    } catch (error) {
      Toast.error('添加管理员失败: ' + error.message)
    } finally {
      setSubmitting(false)
    }
  }

  /**
   * 切换管理员状态。
   */
  const handleToggleStatus = async (admin) => {
    const action = admin.is_active ? '停用' : '启用'
    const confirmed = await ConfirmDialog.confirm({
      title: `${action}管理员`,
      message: `确定要${action}管理员 "${admin.display_name}" (${admin.student_id}) 吗？`,
      confirmText: action,
      type: admin.is_active ? 'warning' : 'info',
    })

    if (!confirmed) return

    try {
      await adminService.setAdminStatus(admin.id, !admin.is_active)
      Toast.success(`管理员已${action}`)
      loadAdmins()
    } catch (error) {
      Toast.error(`${action}管理员失败: ` + error.message)
    }
  }

  /**
   * 删除管理员。
   */
  const handleDeleteAdmin = async (admin) => {
    const confirmed = await ConfirmDialog.confirm({
      title: '删除管理员',
      message: `确定要删除管理员 "${admin.display_name}" (${admin.student_id}) 吗？此操作不可恢复！`,
      confirmText: '删除',
      type: 'danger',
    })

    if (!confirmed) return

    try {
      await adminService.deleteAdmin(admin.id)
      Toast.success('管理员已删除')
      loadAdmins()
    } catch (error) {
      Toast.error('删除管理员失败: ' + error.message)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>管理员列表 ({total})</h2>
        <button className="btn-add" onClick={() => setShowAddModal(true)}>
          + 添加管理员
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <p>加载中...</p>
        </div>
      ) : admins.length === 0 ? (
        <div className="empty-state">
          <p>暂无管理员数据</p>
        </div>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>账号</th>
                <th>姓名</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {admins.map((admin) => (
                <tr key={admin.id}>
                  <td>{admin.student_id}</td>
                  <td>{admin.display_name}</td>
                  <td>
                    <span className={`status-badge ${admin.is_active ? 'active' : 'inactive'}`}>
                      {admin.is_active ? '✓ 启用' : '✗ 停用'}
                    </span>
                  </td>
                  <td>
                    {admin.created_at
                      ? new Date(admin.created_at).toLocaleDateString('zh-CN')
                      : '-'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className={`btn-action ${admin.is_active ? 'warning' : 'primary'}`}
                        onClick={() => handleToggleStatus(admin)}
                      >
                        {admin.is_active ? '停用' : '启用'}
                      </button>
                      <button
                        className="btn-action danger"
                        onClick={() => handleDeleteAdmin(admin)}
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                上一页
              </button>
              <span>
                {page} / {totalPages}
              </span>
              <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {/* 添加管理员模态框 */}
      {showAddModal && (
        <div className="modal-overlay admin-modal" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加管理员</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <form className="admin-form" onSubmit={handleAddAdmin}>
                <div className="form-group">
                  <label>账号</label>
                  <input
                    type="text"
                    placeholder="请输入账号"
                    value={formData.studentId}
                    onChange={(e) =>
                      setFormData({ ...formData, studentId: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>密码</label>
                  <input
                    type="password"
                    placeholder="请输入密码"
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>显示名称</label>
                  <input
                    type="text"
                    placeholder="请输入显示名称"
                    value={formData.displayName}
                    onChange={(e) =>
                      setFormData({ ...formData, displayName: e.target.value })
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
                    {submitting ? '添加中...' : '添加'}
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
