import { API_BASE } from '../config/index.js'
import { uploadFaceImage, withTimeout } from './upload.js'

const UPLOAD_TIMEOUT_MS = 120000

function apiUrl(path) {
  const base = (API_BASE || '').replace(/\/$/, '')
  return `${base}${path}`
}

export function framePreviewUrl(frameId) {
  return apiUrl(`/api/frame-preview/${encodeURIComponent(frameId)}`)
}

export function analyzeFace(filePath) {
  return withTimeout(
    uploadFaceImage(filePath, '/api/analyze', { name: 'face' }),
    UPLOAD_TIMEOUT_MS,
    '测算超时：请确认已启动 python demo/app.py，且 API 地址正确'
  )
}

export function tryOnFace(filePath, frameId) {
  return withTimeout(
    uploadFaceImage(filePath, '/api/tryon?wrap=1', {
      name: 'face',
      formData: { frame_id: frameId },
      header: { 'X-Tryon-Wrap': '1' },
    }).then((data) => {
      if (!data.ok) {
        throw new Error(data.message || data.error || '试戴失败')
      }
      const b64 = data.image_base64
      if (!b64) throw new Error('未收到试戴图')
      return `data:${data.mime || 'image/png'};base64,${b64}`
    }),
    UPLOAD_TIMEOUT_MS,
    '试戴合成超时'
  )
}

export function pingApi() {
  return new Promise((resolve, reject) => {
    uni.request({
      url: apiUrl('/api/catalog'),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(true)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: reject,
    })
  })
}
