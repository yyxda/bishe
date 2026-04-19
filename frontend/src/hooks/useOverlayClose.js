/**
 * 遮罩层关闭逻辑 Hook。
 *
 * 处理模态框遮罩层的点击关闭逻辑，防止文本选择时鼠标拖出对话框导致意外关闭。
 * 只有当 mousedown 和 click 都发生在遮罩层上时才触发关闭。
 */

import { useRef, useCallback } from 'react'

/**
 * 自定义 hook：处理遮罩层点击关闭逻辑。
 *
 * 只有当 mousedown 和 click 都发生在遮罩层上时才触发关闭。
 * 防止在文本选择时鼠标拖出对话框导致意外关闭。
 *
 * @param {Function} onClose 关闭回调函数
 * @returns {object} mousedown 和 click 事件处理函数
 */
export function useOverlayClose(onClose) {
  const mouseDownOnOverlay = useRef(false)

  const handleMouseDown = useCallback((e) => {
    // 只有直接点击 overlay 才标记
    if (e.target === e.currentTarget) {
      mouseDownOnOverlay.current = true
    }
  }, [])

  const handleClick = useCallback(
    (e) => {
      // 只有当 mousedown 和 click 都发生在 overlay 上时才关闭对话框
      if (mouseDownOnOverlay.current && e.target === e.currentTarget) {
        onClose()
      }
      mouseDownOnOverlay.current = false
    },
    [onClose]
  )

  return { handleMouseDown, handleClick }
}
