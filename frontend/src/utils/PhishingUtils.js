/**
 * 钓鱼检测前端工具函数。
 *
 * 统一前端展示的钓鱼邮件概率阈值规则，避免与后端不一致。
 */

export const PHISHING_THRESHOLDS = {
  suspicious: 0.6,
  highRisk: 0.8,
}

/**
 * 根据置信度计算钓鱼等级。
 *
 * @param {number} score 置信度（0-1）
 * @param {string} fallbackLevel 后端返回的等级兜底
 * @returns {string} 钓鱼等级
 */
export function getPhishingLevelByScore(score, fallbackLevel = 'NORMAL') {
  const scoreValue = Number(score)

  if (!Number.isFinite(scoreValue)) {
    return fallbackLevel || 'NORMAL'
  }

  if (scoreValue >= PHISHING_THRESHOLDS.highRisk) {
    return 'HIGH_RISK'
  }

  if (scoreValue >= PHISHING_THRESHOLDS.suspicious) {
    return 'SUSPICIOUS'
  }

  return 'NORMAL'
}

/**
 * 格式化置信度为百分比文本（两位小数）。
 *
 * @param {number} score 置信度（0-1）
 * @returns {string} 百分比文本
 */
export function formatConfidencePercent(score) {
  const scoreValue = Number(score)
  const safeScore = Number.isFinite(scoreValue) ? scoreValue : 0
  return `${(safeScore * 100).toFixed(2)}%`
}
