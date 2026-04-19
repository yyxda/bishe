import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

/**
 * React 应用启动器。
 */
class ReactBootstrap {
  /**
   * @param {string} rootId 挂载节点 ID
   */
  constructor(rootId) {
    this.rootId = rootId
  }

  /**
   * 挂载 React 应用。
   */
  mount() {
    const container = document.getElementById(this.rootId)
    if (!container) {
      throw new Error(`未找到挂载节点：${this.rootId}`)
    }

    createRoot(container).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
}

new ReactBootstrap('root').mount()
