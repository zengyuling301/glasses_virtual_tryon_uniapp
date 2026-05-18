/**
 * API 根地址（不要末尾斜杠）
 *
 * 手机 Safari 打开 http://192.168.x.x:5173 时：
 * - 开发模式会自动用 http://192.168.x.x:5050（同 host，直连 Flask）
 * - 也可在 .env.development 写死：VITE_API_BASE=http://192.168.110.61:5050
 *
 * 电脑本机打开 http://localhost:5173 时：
 * - 默认 ''，走 vite 代理 /api → 127.0.0.1:5050
 */
function resolveApiBase() {
  const fromEnv =
    typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE
  if (fromEnv) {
    return String(fromEnv).replace(/\/$/, '')
  }

  if (typeof window !== 'undefined' && import.meta.env && import.meta.env.DEV) {
    const { hostname, protocol } = window.location
    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      // 手机 / 平板通过局域网 IP 访问前端 → 直连同 IP 的后端
      return `${protocol}//${hostname}:5050`
    }
    return ''
  }

  return 'http://127.0.0.1:5050'
}

export const API_BASE = resolveApiBase()
