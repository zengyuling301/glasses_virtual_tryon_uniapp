import { API_BASE } from '../config/index.js'

function apiUrl(path) {
  const base = (API_BASE || '').replace(/\/$/, '')
  return `${base}${path}`
}

function parseJsonResponse(res, rawBody) {
  const status = res.statusCode != null ? res.statusCode : res.status
  let data = rawBody
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch (e) {
      throw new Error('服务器返回非 JSON')
    }
  }
  if (status >= 400) {
    throw new Error((data && data.message) || `HTTP ${status}`)
  }
  return data
}

/** H5：blob / data URL → FormData → fetch */
async function uploadViaFetch(filePath, path, { name = 'face', formData = {} } = {}) {
  const res = await fetch(filePath)
  const blob = await res.blob()
  const fd = new FormData()
  const type = blob.type || 'image/jpeg'
  fd.append(name, blob, type.includes('png') ? 'face.png' : 'face.jpg')
  Object.keys(formData).forEach((k) => {
    fd.append(k, formData[k])
  })
  const url = apiUrl(path)
  const resp = await fetch(url, { method: 'POST', body: fd })
  const text = await resp.text()
  return parseJsonResponse({ status: resp.status }, text)
}

/** 非 H5：uni.uploadFile */
function uploadViaUni(filePath, path, { name = 'face', formData = {}, header = {} } = {}) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: apiUrl(path),
      filePath,
      name,
      formData,
      header,
      success: (res) => {
        try {
          resolve(parseJsonResponse(res, res.data))
        } catch (e) {
          reject(e)
        }
      },
      fail: (err) => reject(err || new Error('上传失败')),
    })
  })
}

/**
 * 跨端上传人脸图。H5 必须用 fetch+FormData（uni.uploadFile 对 blob 路径常失败）。
 */
export function uploadFaceImage(filePath, path, options = {}) {
  // #ifdef H5
  return uploadViaFetch(filePath, path, options)
  // #endif
  // #ifndef H5
  return uploadViaUni(filePath, path, options)
  // #endif
}

export function withTimeout(promise, ms, message) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(message || '请求超时')), ms)
    }),
  ])
}
