import React, { useState } from 'react';
import './DirectDetectPage.css';

const API_BASE = '/api';

export default function DirectDetectPage() {
  const [emailText, setEmailText] = useState('');
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [detectResult, setDetectResult] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const handleSyncAll = async () => {
    setIsSyncing(true);
    setSyncMessage('正在同步...');
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/email-accounts/sync-all`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      setSyncMessage(data.message || '同步完成');
      setTimeout(() => setSyncMessage(''), 3000);
    } catch (error) {
      setSyncMessage('同步失败: ' + error.message);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDetect = async () => {
    if (!emailText.trim()) {
      alert('请输入邮件内容');
      return;
    }

    setIsDetecting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/bert-training/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          text: emailText,
          sender: sender || 'test@example.com',
          subject: subject || null
        })
      });
      
      const data = await response.json();
      setDetectResult(data);
    } catch (error) {
      alert('检测失败: ' + error.message);
    } finally {
      setIsDetecting(false);
    }
  };

  return (
    <div className="direct-detect-page">
      <div className="page-header">
        <div className="header-top">
          <div>
            <h1>钓鱼邮件直接检测</h1>
            <p>输入邮件内容，快速判断是否为钓鱼邮件</p>
          </div>
          <button 
            className="sync-all-btn"
            onClick={handleSyncAll}
            disabled={isSyncing}
          >
            {isSyncing ? '同步中...' : '🔄 同步所有邮箱'}
          </button>
        </div>
        {syncMessage && <p className="sync-message">{syncMessage}</p>}
      </div>

      <div className="detect-container">
        <div className="instructions">
          <h2>使用说明</h2>
          <p>请在下方文本框中粘贴邮件内容，然后点击"开始检测"按钮。</p>
          <ul>
            <li>支持粘贴完整的邮件内容</li>
            <li>系统将分析邮件文本特征</li>
            <li>快速返回检测结果和置信度</li>
          </ul>
        </div>

        <div className="input-section">
          <h2>输入邮件内容</h2>
          <div className="email-fields">
            <div className="field-group">
              <label>发件人邮箱（可选）</label>
              <input
                type="email"
                className="email-field-input"
                placeholder="例如: service@jd.com"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
              />
              <small>如果发件人在白名单中，将跳过检测</small>
            </div>
            <div className="field-group">
              <label>邮件主题（可选）</label>
              <input
                type="text"
                className="email-field-input"
                placeholder="例如: 订单发货通知"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
            </div>
          </div>
          <textarea
            className="email-input"
            placeholder="在此处粘贴邮件内容..."
            value={emailText}
            onChange={(e) => setEmailText(e.target.value)}
            rows={12}
          />
          <button 
            className="detect-btn"
            onClick={handleDetect}
            disabled={isDetecting}
          >
            {isDetecting ? '检测中...' : '开始检测'}
          </button>
        </div>

        {detectResult && detectResult.result && (
          <div className={`result-box ${detectResult.result.level === 'HIGH_RISK' || detectResult.result.level === 'SUSPICIOUS' ? 'danger' : 'safe'}`}>
            <h3>检测结果</h3>
            <div className="result-content">
              <p className="result-label">
                {detectResult.result.level === 'NORMAL' ? '✅ 正常邮件' : 
                 detectResult.result.level === 'HIGH_RISK' ? '⚠️ 高危钓鱼邮件' : 
                 '⚡ 疑似钓鱼邮件'}
              </p>
              <p className="confidence">
                钓鱼概率: {(detectResult.result.score * 100).toFixed(2)}%
              </p>
              <p className="reason">
                {detectResult.result.reason}
              </p>
              {(detectResult.result.level === 'HIGH_RISK' || detectResult.result.level === 'SUSPICIOUS') && (
                <div className="warning-message">
                  <p>⚠️ 警告：这是一封钓鱼邮件，请勿点击其中的链接或下载附件！</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}