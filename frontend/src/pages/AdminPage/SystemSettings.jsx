import React, { useState, useEffect } from 'react';
import './SystemSettings.css';

export default function SystemSettings() {
  const [settings, setSettings] = useState({
    enable_long_url_detection: false,
    enable_rule_based_detection: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const response = await fetch(`${API_BASE}/api/admin/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings({
          enable_long_url_detection: data.enable_long_url_detection,
          enable_rule_based_detection: data.enable_rule_based_detection,
        });
      }
    } catch (error) {
      console.error('获取系统设置失败:', error);
      setMessage('获取系统设置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    
    try {
      const token = localStorage.getItem('token');
      const API_BASE = 'http://localhost:10003';
      const response = await fetch(`${API_BASE}/api/admin/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(settings),
      });
      
      if (response.ok) {
        setMessage('✅ 系统设置已更新');
      } else {
        setMessage('❌ 更新系统设置失败');
      }
    } catch (error) {
      console.error('更新系统设置失败:', error);
      setMessage('❌ 更新系统设置失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="admin-card">
        <div className="admin-card-header">
          <h2>⚙️ 系统设置</h2>
        </div>
        <div className="admin-form">
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>⚙️ 系统设置</h2>
      </div>

      <div className="admin-form">
        <div className="setting-item">
          <div className="setting-row">
            <div className="setting-info">
              <h3>🔗 长链接检测</h3>
              <p>
                启用后，系统会检测邮件中的长链接，提高钓鱼邮件识别准确率。
              </p>
            </div>
            <div className="setting-control">
              <label className="switch">
                <input
                  type="checkbox"
                  checked={settings.enable_long_url_detection}
                  onChange={(e) => setSettings({
                    ...settings,
                    enable_long_url_detection: e.target.checked,
                  })}
                />
                <span className="slider round"></span>
              </label>
            </div>
          </div>
        </div>

        <div className="setting-item">
          <div className="setting-row">
            <div className="setting-info">
              <h3>🎯 规则检测</h3>
              <p>
                启用后，系统会使用混合检测策略（BERT + 规则），提高检测准确率，但检测速度会稍慢。
                禁用时仅使用BERT检测，检测速度快但准确率可能略低。
              </p>
            </div>
            <div className="setting-control">
              <label className="switch">
                <input
                  type="checkbox"
                  checked={settings.enable_rule_based_detection}
                  onChange={(e) => setSettings({
                    ...settings,
                    enable_rule_based_detection: e.target.checked,
                  })}
                />
                <span className="slider round"></span>
              </label>
            </div>
          </div>
        </div>

        {message && (
          <div className="setting-message">
            {message}
          </div>
        )}

        <div className="setting-actions">
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}