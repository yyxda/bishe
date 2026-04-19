/**
 * 学生管理组件。
 *
 * 提供学号的添加、停用功能。
 */

import React, { useState, useEffect, useCallback } from 'react'
import AdminService from '../../services/AdminService.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import { useOverlayClose } from '../../hooks/useOverlayClose'

const adminService = new AdminService()

/**
 * 学生管理组件。
 *
 * @returns {JSX.Element} 学生管理界面
 */
export default function StudentManagement() {
  const [students, setStudents] = useState([])
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
   * 加载学生列表。
   */
  const loadStudents = useCallback(async () => {
    setLoading(true)
    try {
      const response = await adminService.getStudents(page, pageSize)
      setStudents(response.users || [])
      setTotal(response.total || 0)
    } catch (error) {
      Toast.error('加载学生列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    loadStudents()
  }, [loadStudents])

  /**
   * 处理添加学生表单提交。
   */
  const handleAddStudent = async (e) => {
    e.preventDefault()
    if (submitting) return

    if (!formData.studentId || !formData.password || !formData.displayName) {
      Toast.error('请填写完整信息')
      return
    }

    setSubmitting(true)
    try {
      await adminService.createStudent(
        formData.studentId,
        formData.password,
        formData.displayName
      )
      Toast.success('学生添加成功')
      setShowAddModal(false)
      setFormData({ studentId: '', password: '', displayName: '' })
      loadStudents()
    } catch (error) {
      Toast.error('添加学生失败: ' + error.message)
    } finally {
      setSubmitting(false)
    }
  }

  /**
   * 切换学生状态。
   */
  const handleToggleStatus = async (student) => {
    const action = student.is_active ? '停用' : '启用'
    const confirmed = await ConfirmDialog.confirm({
      title: `${action}学生`,
      message: `确定要${action}学生 "${student.display_name}" (${student.student_id}) 吗？`,
      confirmText: action,
      type: student.is_active ? 'warning' : 'info',
    })

    if (!confirmed) return

    try {
      await adminService.setStudentStatus(student.id, !student.is_active)
      Toast.success(`学生已${action}`)
      loadStudents()
    } catch (error) {
      Toast.error(`${action}学生失败: ` + error.message)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>学生列表 ({total})</h2>
        <button className="btn-add" onClick={() => setShowAddModal(true)}>
          + 添加学生
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <p>加载中...</p>
        </div>
      ) : students.length === 0 ? (
        <div className="empty-state">
          <p>暂无学生数据</p>
        </div>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>学号</th>
                <th>姓名</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.student_id}</td>
                  <td>{student.display_name}</td>
                  <td>
                    <span className={`status-badge ${student.is_active ? 'active' : 'inactive'}`}>
                      {student.is_active ? '✓ 启用' : '✗ 停用'}
                    </span>
                  </td>
                  <td>
                    {student.created_at
                      ? new Date(student.created_at).toLocaleDateString('zh-CN')
                      : '-'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className={`btn-action ${student.is_active ? 'warning' : 'primary'}`}
                        onClick={() => handleToggleStatus(student)}
                      >
                        {student.is_active ? '停用' : '启用'}
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

      {/* 添加学生模态框 */}
      {showAddModal && (
        <div className="modal-overlay admin-modal" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加学生</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <form className="admin-form" onSubmit={handleAddStudent}>
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