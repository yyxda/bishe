/**
 * 用户管理组件。
 *
 * 提供学号的添加、删除、停用功能。
 */

import React, { useState, useEffect, useCallback } from 'react'
import AdminService from '../../services/AdminService.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { useOverlayClose } from '../../hooks/useOverlayClose'

const adminService = new AdminService()

/**
 * 用户管理组件。
 *
 * @returns {JSX.Element} 用户管理界面
 */
export default function UserManagement() {
  const [users, setUsers] = useState([])
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
   * 加载用户列表。
   */
  const loadUsers = useCallback(async () => {
    setLoading(true)
    try {
      const response = await adminService.getUsers(page, pageSize)
      setUsers(response.users || [])
      setTotal(response.total || 0)
    } catch (error) {
      Toast.error('加载用户列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  /**
   * 处理添加用户表单提交。
   */
  const handleAddUser = async (e) => {
    e.preventDefault()
    if (submitting) return

    if (!formData.studentId || !formData.password || !formData.displayName) {
      Toast.error('请填写完整信息')
      return
    }

    setSubmitting(true)
    try {
      await adminService.createUser(
        formData.studentId,
        formData.password,
        formData.displayName
      )
      Toast.success('用户添加成功')
      setShowAddModal(false)
      setFormData({ studentId: '', password: '', displayName: '' })
      loadUsers()
    } catch (error) {
      Toast.error('添加用户失败: ' + error.message)
    } finally {
      setSubmitting(false)
    }
  }

  /**
   * 切换用户状态。
   */
  const handleToggleStatus = async (user) => {
    const action = user.is_active ? '停用' : '启用'
    const confirmed = await ConfirmDialog.show({
      title: `${action}用户`,
      message: `确定要${action}用户 "${user.display_name}" (${user.student_id}) 吗？`,
      confirmText: action,
      type: user.is_active ? 'warning' : 'info',
    })

    if (!confirmed) return

    try {
      await adminService.setUserStatus(user.id, !user.is_active)
      Toast.success(`用户已${action}`)
      loadUsers()
    } catch (error) {
      Toast.error(`${action}用户失败: ` + error.message)
    }
  }

  /**
   * 删除用户。
   */
  const handleDeleteUser = async (user) => {
    const confirmed = await ConfirmDialog.show({
      title: '删除用户',
      message: `确定要删除用户 "${user.display_name}" (${user.student_id}) 吗？此操作不可恢复！`,
      confirmText: '删除',
      type: 'danger',
    })

    if (!confirmed) return

    try {
      await adminService.deleteUser(user.id)
      Toast.success('用户已删除')
      loadUsers()
    } catch (error) {
      Toast.error('删除用户失败: ' + error.message)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>用户列表 ({total})</h2>
        <button className="btn-add" onClick={() => setShowAddModal(true)}>
          + 添加用户
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <p>加载中...</p>
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <p>暂无用户数据</p>
        </div>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>学号</th>
                <th>姓名</th>
                <th>角色</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.student_id}</td>
                  <td>{user.display_name}</td>
                  <td>{user.role === 'admin' ? '管理员' : '普通用户'}</td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? '✓ 启用' : '✗ 停用'}
                    </span>
                  </td>
                  <td>
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString('zh-CN')
                      : '-'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className={`btn-action ${user.is_active ? 'warning' : 'primary'}`}
                        onClick={() => handleToggleStatus(user)}
                      >
                        {user.is_active ? '停用' : '启用'}
                      </button>
                      <button
                        className="btn-action danger"
                        onClick={() => handleDeleteUser(user)}
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

      {/* 添加用户模态框 */}
      {showAddModal && (
        <div className="modal-overlay admin-modal" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加用户</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <form className="admin-form" onSubmit={handleAddUser}>
                <div className="form-group">
                  <label>学号</label>
                  <input
                    type="text"
                    placeholder="请输入学号"
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
