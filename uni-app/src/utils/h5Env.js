/** H5 环境：摄像头、安全上下文 */

export function isSecureContext() {
  if (typeof window === 'undefined') return false
  return window.isSecureContext === true
}

/**
 * iOS Safari 通过 http://192.168.x.x 访问时，getUserMedia 不可用（非安全上下文）。
 * 这不是业务 bug，是浏览器安全策略。
 */
export function getH5CameraBlockReason() {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') {
    return { code: 'unknown', message: '非浏览器环境' }
  }
  if (!isSecureContext()) {
    return {
      code: 'insecure',
      message: '当前为 HTTP 访问，iOS Safari 不允许实时摄像头',
      hint: '请用下方「前置拍照」或「相册」；或使用 HTTPS 访问本页',
    }
  }
  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== 'function') {
    return {
      code: 'unsupported',
      message: '当前浏览器不支持实时摄像头 API',
      hint: '请用「前置拍照」或「相册」',
    }
  }
  return null
}

/** 用原生 input[capture=user] 调起前置相机（无实时预览，但 iOS HTTP 可用） */
export function pickImageViaNativeInput({ capture = 'user', album = false } = {}) {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    if (!album && capture) {
      input.setAttribute('capture', capture)
    }
    input.style.display = 'none'
    document.body.appendChild(input)
    input.onchange = () => {
      const file = input.files && input.files[0]
      document.body.removeChild(input)
      if (!file) {
        reject(new Error('未选择图片'))
        return
      }
      resolve(URL.createObjectURL(file))
    }
    input.click()
  })
}
