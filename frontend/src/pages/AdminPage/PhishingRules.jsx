import React, { useState, useEffect } from 'react';
import './PhishingRules.css';

export default function PhishingRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [formData, setFormData] = useState({
    rule_name: '',
    rule_type: 'CONTENT',
    rule_pattern: '',
    rule_description: '',
    severity: 5,
  });

  useEffect(() => {
    fetchRules();
  }, [filter]);

  const fetchRules = async () => {
    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const url = filter === 'ALL' 
        ? `${API_BASE}/api/phishing-rules`
        : `${API_BASE}/api/phishing-rules?rule_type=${filter}`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setRules(data.rules);
      }
    } catch (error) {
      console.error('获取规则失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingRule(null);
    setFormData({
      rule_name: '',
      rule_type: 'CONTENT',
      rule_pattern: '',
      rule_description: '',
      severity: 5,
    });
    setShowModal(true);
  };

  const handleEdit = (rule) => {
    setEditingRule(rule);
    setFormData({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      rule_pattern: rule.rule_pattern,
      rule_description: rule.rule_description || '',
      severity: rule.severity,
    });
    setShowModal(true);
  };

  const handleDelete = async (ruleId) => {
    if (!window.confirm('确定要删除这条规则吗？')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const response = await fetch(`${API_BASE}/api/phishing-rules/${ruleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        fetchRules();
      }
    } catch (error) {
      console.error('删除规则失败:', error);
      alert('删除规则失败');
    }
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const url = editingRule
        ? `${API_BASE}/api/phishing-rules/${editingRule.id}`
        : `${API_BASE}/api/phishing-rules`;
      
      const response = await fetch(url, {
        method: editingRule ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        setShowModal(false);
        fetchRules();
      } else {
        alert('保存规则失败');
      }
    } catch (error) {
      console.error('保存规则失败:', error);
      alert('保存规则失败');
    }
  };

  const handleToggleActive = async (rule) => {
    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const response = await fetch(`${API_BASE}/api/phishing-rules/${rule.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          is_active: !rule.is_active,
        }),
      });
      
      if (response.ok) {
        fetchRules();
      }
    } catch (error) {
      console.error('更新规则状态失败:', error);
      alert('更新规则状态失败');
    }
  };

  const getRuleTypeLabel = (type) => {
    const labels = {
      'URL': '🔗 URL规则',
      'SENDER': '📧 发件人规则',
      'CONTENT': '📝 内容规则',
      'STRUCTURE': '🏗️ 结构规则',
    };
    return labels[type] || type;
  };

  const getSeverityColor = (severity) => {
    if (severity >= 8) return '#d32f2f';
    if (severity >= 6) return '#f57c00';
    if (severity >= 4) return '#faad14';
    return '#52c41a';
  };

  if (loading) {
    return (
      <div className="phishing-rules-page">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  return (
    <div className="phishing-rules-page">
      <div className="page-header">
        <h1>🎯 钓鱼检测规则管理</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          ➕ 添加规则
        </button>
      </div>

      <div className="filter-bar">
        <button 
          className={`filter-btn ${filter === 'ALL' ? 'active' : ''}`}
          onClick={() => setFilter('ALL')}
        >
          全部规则
        </button>
        <button 
          className={`filter-btn ${filter === 'URL' ? 'active' : ''}`}
          onClick={() => setFilter('URL')}
        >
          URL规则
        </button>
        <button 
          className={`filter-btn ${filter === 'SENDER' ? 'active' : ''}`}
          onClick={() => setFilter('SENDER')}
        >
          发件人规则
        </button>
        <button 
          className={`filter-btn ${filter === 'CONTENT' ? 'active' : ''}`}
          onClick={() => setFilter('CONTENT')}
        >
          内容规则
        </button>
        <button 
          className={`filter-btn ${filter === 'STRUCTURE' ? 'active' : ''}`}
          onClick={() => setFilter('STRUCTURE')}
        >
          结构规则
        </button>
      </div>

      <div className="rules-list">
        {rules.length === 0 ? (
          <div className="empty-state">
            <p>暂无规则</p>
            <button className="btn btn-primary" onClick={handleCreate}>
              添加第一条规则
            </button>
          </div>
        ) : (
          rules.map((rule) => (
            <div key={rule.id} className={`rule-card ${!rule.is_active ? 'disabled' : ''}`}>
              <div className="rule-header">
                <div className="rule-title">
                  <span className="rule-type-badge">{getRuleTypeLabel(rule.rule_type)}</span>
                  <h3>{rule.rule_name}</h3>
                </div>
                <div className="rule-actions">
                  <button 
                    className="action-btn"
                    onClick={() => handleToggleActive(rule)}
                    title={rule.is_active ? '禁用' : '启用'}
                  >
                    {rule.is_active ? '🔴' : '🟢'}
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handleEdit(rule)}
                    title="编辑"
                  >
                    ✏️
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handleDelete(rule.id)}
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              
              <div className="rule-body">
                <div className="rule-pattern">
                  <label>规则模式：</label>
                  <code>{rule.rule_pattern}</code>
                </div>
                
                {rule.rule_description && (
                  <div className="rule-description">
                    <label>描述：</label>
                    <p>{rule.rule_description}</p>
                  </div>
                )}
                
                <div className="rule-severity">
                  <label>严重程度：</label>
                  <div 
                    className="severity-bar"
                    style={{ backgroundColor: getSeverityColor(rule.severity) }}
                  >
                    <span className="severity-value">{rule.severity}/10</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingRule ? '编辑规则' : '添加规则'}</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label>规则名称 *</label>
                <input
                  type="text"
                  value={formData.rule_name}
                  onChange={(e) => setFormData({...formData, rule_name: e.target.value})}
                  placeholder="例如：紧急性词汇检测"
                />
              </div>

              <div className="form-group">
                <label>规则类型 *</label>
                <select
                  value={formData.rule_type}
                  onChange={(e) => setFormData({...formData, rule_type: e.target.value})}
                >
                  <option value="CONTENT">📝 内容规则</option>
                  <option value="URL">🔗 URL规则</option>
                  <option value="SENDER">📧 发件人规则</option>
                  <option value="STRUCTURE">🏗️ 结构规则</option>
                </select>
              </div>

              <div className="form-group">
                <label>规则模式（正则表达式）*</label>
                <input
                  type="text"
                  value={formData.rule_pattern}
                  onChange={(e) => setFormData({...formData, rule_pattern: e.target.value})}
                  placeholder="例如：(立即|紧急|马上)"
                />
                <small>支持正则表达式，用于匹配邮件内容</small>
              </div>

              <div className="form-group">
                <label>规则描述</label>
                <textarea
                  value={formData.rule_description}
                  onChange={(e) => setFormData({...formData, rule_description: e.target.value})}
                  placeholder="描述这个规则的用途..."
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>严重程度：{formData.severity}/10</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={formData.severity}
                  onChange={(e) => setFormData({...formData, severity: parseInt(e.target.value)})}
                  className="severity-slider"
                />
                <div className="severity-labels">
                  <span>低</span>
                  <span>高</span>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleSave}>
                {editingRule ? '更新' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}