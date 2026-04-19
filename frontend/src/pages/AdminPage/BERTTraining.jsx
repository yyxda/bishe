import React, { useState, useEffect } from 'react';
import './BERTTraining.css';

const API_BASE = '/api';

export default function BERTTraining() {
  const [activeTab, setActiveTab] = useState('detect');
  const [emailText, setEmailText] = useState('');
  const [detectResult, setDetectResult] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [visualizationData, setVisualizationData] = useState({});
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);
  
  // 轮播图相关状态
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlay, setIsAutoPlay] = useState(true);
  
  // 轮播图配置
  const slides = [
    { id: 'loss', title: '📈 训练损失曲线', key: 'loss', description: '显示模型训练过程中的损失变化趋势' },
    { id: 'accuracy', title: '📊 训练准确率曲线', key: 'accuracy', description: '显示模型训练过程中的准确率变化趋势' },
    { id: 'roc', title: '🎯 ROC曲线', key: 'roc', description: '显示真正例率和假正例率的关系' },
    { id: 'pr', title: '📉 PR曲线', key: 'pr', description: '显示精确率和召回率的权衡关系' },
    { id: 'confusion', title: '🔢 混淆矩阵', key: 'confusion', description: '显示模型预测结果的分类情况' },
    { id: 'metrics_bar', title: '📊 性能指标', key: 'metrics_bar', description: '显示模型的整体性能指标' }
  ];
  
  // 自动轮播效果
  useEffect(() => {
    if (!isAutoPlay || activeTab !== 'visualization') return;
    
    const interval = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % slides.length);
    }, 5000); // 每5秒自动切换
    
    return () => clearInterval(interval);
  }, [isAutoPlay, activeTab]);
  
  // 手动切换轮播图
  const nextSlide = () => {
    setCurrentSlide(prev => (prev + 1) % slides.length);
  };
  
  const prevSlide = () => {
    setCurrentSlide(prev => (prev - 1 + slides.length) % slides.length);
  };
  
  // 跳转到指定幻灯片
  const goToSlide = (index) => {
    setCurrentSlide(index);
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
        body: JSON.stringify({ text: emailText })
      });
      
      const data = await response.json();
      console.log('检测结果:', data);
      setDetectResult(data.result);
    } catch (error) {
      alert('检测失败: ' + error.message);
    } finally {
      setIsDetecting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsDetecting(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE}/bert-training/detect/file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      setDetectResult(data.result);
    } catch (error) {
      alert('文件检测失败: ' + error.message);
    } finally {
      setIsDetecting(false);
    }
  };

  const handleTrain = async () => {
    setIsTraining(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/bert-training/train`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('训练结果:', data);
      alert(data.message || '训练完成');
      if (data.metrics) {
        setMetrics(data.metrics);
      }
      loadMetrics();
    } catch (error) {
      console.error('训练失败:', error);
      alert('训练失败: ' + error.message);
    } finally {
      setIsTraining(false);
    }
  };

  const loadMetrics = async () => {
    setIsLoadingMetrics(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/bert-training/metrics`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      if (data.status === 'trained' && data.metrics) {
        setMetrics(data.metrics);
      }
    } catch (error) {
      console.error('加载指标失败:', error);
    } finally {
      setIsLoadingMetrics(false);
    }
  };

  const loadVisualization = async (type) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/bert-training/visualization/${type}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        console.error(`加载可视化 ${type} 失败: HTTP ${response.status}`);
        return;
      }
      
      const data = await response.json();
      if (data.status === 'success' && data.image) {
        setVisualizationData(prev => ({ ...prev, [type]: data.image }));
      }
    } catch (error) {
      console.error('加载可视化数据失败:', error);
    }
  };

  useEffect(() => {
    if (activeTab === 'metrics' || activeTab === 'visualization') {
      loadMetrics();
      loadVisualization('loss');
      loadVisualization('accuracy');
      loadVisualization('roc');
      loadVisualization('pr');
      loadVisualization('confusion');
      loadVisualization('metrics_bar');
    }
  }, [activeTab]);

  return (
    <div className="bert-training">
      <div className="bert-training-header">
        <h2>🤖 BERT钓鱼邮件检测系统</h2>
        <p>基于BERT的中文钓鱼邮件智能检测与分析</p>
      </div>

      <div className="bert-training-tabs">
        <button 
          className={`bert-tab ${activeTab === 'detect' ? 'active' : ''}`}
          onClick={() => setActiveTab('detect')}
        >
          📧 邮件检测
        </button>
        <button 
          className={`bert-tab ${activeTab === 'train' ? 'active' : ''}`}
          onClick={() => setActiveTab('train')}
        >
          🎯 模型训练
        </button>
        <button 
          className={`bert-tab ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          📊 性能指标
        </button>
        <button 
          className={`bert-tab ${activeTab === 'visualization' ? 'active' : ''}`}
          onClick={() => setActiveTab('visualization')}
        >
          📈 可视化分析
        </button>
      </div>

      <div className="bert-training-content">
        {activeTab === 'detect' && (
          <div className="detect-section">
            <h3>输入邮件内容进行检测</h3>
            
            <div className="detect-methods">
              <div className="method-card">
                <h4>方式一：文本输入</h4>
                <textarea 
                  className="email-input" 
                  placeholder="请粘贴邮件内容..." 
                  value={emailText} 
                  onChange={(e) => setEmailText(e.target.value)} 
                  rows={10} 
                />
                <button 
                  className="action-btn"
                  onClick={handleDetect}
                  disabled={isDetecting}
                >
                  {isDetecting ? '检测中...' : '开始检测'}
                </button>
              </div>
              
              <div className="method-card">
                <h4>方式二：文件上传</h4>
                <input 
                  type="file" 
                  accept=".txt,.eml,.html,.csv"
                  onChange={handleFileUpload}
                  disabled={isDetecting}
                  className="file-input"
                />
                <p className="hint">支持 .txt, .eml, .html, .csv 格式</p>
              </div>
            </div>

            {detectResult && (
              <div className={`result-box ${detectResult.level === 'HIGH_RISK' ? 'danger' : detectResult.level === 'SUSPICIOUS' ? 'warning' : 'safe'}`}>
                <h4>检测结果</h4>
                {detectResult.level === 'HIGH_RISK' ? (
                  <p className="result-label">
                    <span className="warning-icon">🚨</span>
                    高危钓鱼邮件 - 请勿点击任何链接
                  </p>
                ) : detectResult.level === 'SUSPICIOUS' ? (
                  <p className="result-label">
                    <span className="warning-icon">⚠️</span>
                    疑似钓鱼邮件 - 请谨慎对待
                  </p>
                ) : (
                  <p className="result-label">
                    <span className="warning-icon">✅</span>
                    正常邮件 - 风险较低
                  </p>
                )}
                <p className="confidence">
                  钓鱼邮件概率: {(detectResult.score * 100).toFixed(2)}%
                </p>
                {detectResult.reason && <p className="message">原因: {detectResult.reason}</p>}
              </div>
            )}
          </div>
        )}

        {activeTab === 'train' && (
          <div className="train-section">
            <h3>🎯 BERT模型训练</h3>
            <div className="train-info">
              <p>点击下方按钮开始训练BERT钓鱼邮件检测模型</p>
              <ul>
                <li>训练数据集: 中文钓鱼邮件数据集</li>
                <li>预训练模型: distilbert-base-multilingual-cased</li>
                <li>训练轮数: 2 epochs</li>
                <li>批次大小: 8</li>
                <li>学习率: 3e-5</li>
                <li>预期准确率: 92-96%</li>
              </ul>
            </div>
            <button 
              className="action-btn train-btn"
              onClick={handleTrain}
              disabled={isTraining}
            >
              {isTraining ? '训练中...' : '开始训练模型'}
            </button>
            
            {metrics && (
              <div className="metrics-summary">
                <h4>✅ 训练完成！模型性能：</h4>
                <div className="metrics-grid">
                  <div className="metric-item">
                    <span className="metric-label">准确率</span>
                    <span className="metric-value">{(metrics.accuracy * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">精确率</span>
                    <span className="metric-value">{(metrics.precision * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">召回率</span>
                    <span className="metric-value">{(metrics.recall * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">F1得分</span>
                    <span className="metric-value">{(metrics.f1_score * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="metrics-section">
            <h3>📊 模型性能指标</h3>
            {isLoadingMetrics ? (
              <p>加载中...</p>
            ) : metrics ? (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon">📊</div>
                  <div className="metric-info">
                    <span className="metric-label">准确率</span>
                    <span className="metric-value">{(metrics.accuracy * 100).toFixed(2)}%</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🎯</div>
                  <div className="metric-info">
                    <span className="metric-label">精确率</span>
                    <span className="metric-value">{(metrics.precision * 100).toFixed(2)}%</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🔄</div>
                  <div className="metric-info">
                    <span className="metric-label">召回率</span>
                    <span className="metric-value">{(metrics.recall * 100).toFixed(2)}%</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">📈</div>
                  <div className="metric-info">
                    <span className="metric-label">F1得分</span>
                    <span className="metric-value">{(metrics.f1_score * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-metrics">
                <p>暂无模型指标，请先训练模型</p>
                <button onClick={() => setActiveTab('train')}>去训练</button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'visualization' && (
          <div className="visualization-section">
            <h3>📈 模型可视化分析</h3>
            
            <div className="charts-grid">
              <div className="chart-card">
                <h4>📈 损失函数变化曲线</h4>
                <div className="chart-image">
                  {visualizationData.loss ? (
                    <img src={`data:image/png;base64,${visualizationData.loss}`} alt="Loss曲线" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
              
              <div className="chart-card">
                <h4>📊 训练准确率曲线</h4>
                <div className="chart-image">
                  {visualizationData.accuracy ? (
                    <img src={`data:image/png;base64,${visualizationData.accuracy}`} alt="Accuracy曲线" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
              
              <div className="chart-card">
                <h4>🎯 ROC曲线</h4>
                <div className="chart-image">
                  {visualizationData.roc ? (
                    <img src={`data:image/png;base64,${visualizationData.roc}`} alt="ROC曲线" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
              
              <div className="chart-card">
                <h4>📉 PR曲线</h4>
                <div className="chart-image">
                  {visualizationData.pr ? (
                    <img src={`data:image/png;base64,${visualizationData.pr}`} alt="PR曲线" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
              
              <div className="chart-card">
                <h4>🔢 混淆矩阵</h4>
                <div className="chart-image">
                  {visualizationData.confusion ? (
                    <img src={`data:image/png;base64,${visualizationData.confusion}`} alt="混淆矩阵" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
              
              <div className="chart-card">
                <h4>📊 性能指标</h4>
                <div className="chart-image">
                  {visualizationData.metrics_bar ? (
                    <img src={`data:image/png;base64,${visualizationData.metrics_bar}`} alt="性能指标" />
                  ) : (
                    <p>暂无数据</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}