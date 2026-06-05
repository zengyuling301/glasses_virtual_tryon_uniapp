/**
 * 景深能力探测模块
 *
 * 用于 P0 协议确认后检测当前终端是否可获取镜头景深信息，
 * 决定 P1 拍照页走 depth（有景深无参照物）还是 reference（无景深须持参照物）模式。
 *
 * 调用方式：
 *   const { hasDepth, method } = await detectDepthCapability()
 *   // hasDepth: true  → capture_mode = 'depth'
 *   // hasDepth: false → capture_mode = 'reference'
 */

/**
 * 检测当前运行环境是否具备镜头景深获取能力
 *
 * @param {Object} [options]
 * @param {string} [options.forceMode] - 强制覆盖结果（调试用）：'depth' | 'reference'
 * @returns {Promise<{hasDepth: boolean, method: string, detail: string}>}
 */
export async function detectDepthCapability(options = {}) {
  const { forceMode } = options

  // 调试强制覆盖（优先级最高）
  if (forceMode === 'depth') {
    return { hasDepth: true, method: 'force', detail: '调试强制：有景深' }
  }
  if (forceMode === 'reference') {
    return { hasDepth: false, method: 'force', detail: '调试强制：无景深（参照物模式）' }
  }

  // #ifdef APP-PLUS
  return detectDepthNative()
  // #endif

  // #ifdef H5
  return detectDepthH5()
  // #endif

  // 兜底：未知环境默认无景深（保守策略）
  return { hasDepth: false, method: 'fallback', detail: '未知运行环境，默认无景深' }
}

// ==================== APP 原生环境检测 ====================

/**
 * Android / iOS 原生 APP 环境下的景深能力检测
 *
 * Android：通过 Camera2 API 查询 DEPTH_OUTPUT 支持
 * iOS：通过 AVCaptureDevice 查询 activeFormat.supportedDepthDataFormats
 *
 * @returns {Promise<{hasDepth: boolean, method: string, detail: string}>}
 */
async function detectDepthNative() {
  try {
    // #ifdef APP-PLUS
    const platform = uni.getSystemInfoSync().platform // 'ios' | 'android'

    if (platform === 'ios') {
      return detectDepthIOS()
    }
    if (platform === 'android') {
      return detectDepthAndroid()
    }

    return { hasDepth: false, method: 'native-unknown', detail: `未识别的平台: ${platform}` }
    // #endif

    return { hasDepth: false, method: 'native-fail', detail: '非 APP 原生环境' }
  } catch (e) {
    console.warn('[depthDetect] 原生景深检测异常:', e)
    // 检测异常时保守降级为无景深
    return { hasDepth: false, method: 'native-error', detail: `检测异常: ${e.message || 'unknown'}` }
  }
}

/**
 * iOS 原生景深检测
 * 通过 plus.ios.invoke 检查 AVCaptureDevice 是否支持深度数据输出
 */
function detectDepthIOS() {
  // #ifdef APP-PLUS
  try {
    const AVCaptureDevice = plus.ios.import('AVCaptureDevice')
    const device = AVCaptureDevice.defaultDeviceForMediaType('vide')

    if (!device) {
      return { hasDepth: false, method: 'ios-nodevice', detail: '无法获取默认摄像头设备' }
    }

    const format = device.activeFormat()
    if (!format) {
      return { hasDepth: false, method: 'ios-noformat', detail: '无法获取当前格式' }
    }

    // 检查 supportedDepthDataFormats 是否非空
    const depthFormats = plus.ios.invoke(format, 'supportedDepthDataFormats')
    const count = plus.ios.invoke(depthFormats, 'count')

    const supported = count > 0
    return {
      hasDepth: supported,
      method: 'ios-depth',
      detail: supported ? `iOS 支持 AVDepthData (${count} 种格式)` : 'iOS 不支持深度数据',
    }
  } catch (e) {
    console.warn('[depthDetect] iOS 景深检测失败:', e)
    return { hasDepth: false, method: 'ios-error', detail: `iOS 检测异常: ${e.message}` }
  }
  // #endif

  return { hasDepth: false, method: 'ios-unavailable', detail: '非 iOS 原生环境' }
}

/**
 * Android 原生景深检测
 * 通过 Camera2 API 查询 DEPTH_OUTPUT 能力
 */
function detectDepthAndroid() {
  // #ifdef APP-PLUS
  try {
    // 通过原生模块或反射调用 Camera2 API 检查 DEPTH_OUTPUT
    // 简化实现：检查 Android 版本 + 相机特性
    const sysInfo = uni.getSystemInfoSync()
    const androidVersion = parseInt(sysInfo.system?.match(/Android\s+(\d+)/)?.[1] || '0', 10)

    // Camera2 DEPTH_OUTPUT 需要 API 23+ (Android 6.0)
    if (androidVersion < 23) {
      return { hasDepth: false, method: 'android-version', detail: `Android ${androidVersion} < 23，不支持 Camera2 深度` }
    }

    // 进一步通过原生插件或反射查询具体相机特性
    // 此处做基础版本判断；完整检测需配合原生插件或 UTS
    // TODO: 接入原生插件后可精确判断 DEPTH_10/DEPTH_16 等
    const hasPotentialDepth = androidVersion >= 26 // Android 8.0+ 更可能支持
    return {
      hasDepth: hasPotentialDepth,
      method: 'android-version-gate',
      detail: `Android ${androidVersion}，${hasPotentialDepth ? '可能支持' : '大概率不支持'} Camera2 深度输出`,
    }
  } catch (e) {
    console.warn('[depthDetect] Android 景深检测失败:', e)
    return { hasDepth: false, method: 'android-error', detail: `Android 检测异常: ${e.message}` }
  }
  // #endif

  return { hasDepth: false, method: 'android-unavailable', detail: '非 Android 原生环境' }
}

// ==================== H5 浏览器环境检测 ====================

/**
 * H5 浏览器环境下的景深能力检测
 *
 * 大多数浏览器（包括移动端 Safari/Chrome）的 getUserMedia 不支持 depth 约束，
 * 因此 H5 环境基本始终返回 false。
 *
 * @returns {Promise<{hasDepth: boolean, method: string, detail: string}>}
 */
async function detectDepthH5() {
  try {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      return { hasDepth: false, method: 'h5-nomediadevices', detail: '浏览器不支持 mediaDevices' }
    }

    const supported = navigator.mediaDevices.getSupportedConstraints()

    if (!supported.depth) {
      return {
        hasDepth: false,
        method: 'h5-nodepth',
        detail: 'H5 getUserMedia 不支持 depth 约束，无法获取镜头景深',
      }
    }

    // 即使声明支持 depth，实际能拿到深度流的概率极低
    // 尝试验证：请求带 depth 的流看是否会报错
    try {
      // 仅检查约束是否被接受，不真正开启流（避免权限弹窗）
      const trackConstraints = { video: { facingMode: 'user', depth: true } }
      // 注意：这里不调用 getUserMedia，仅做特性检测
      // 实际深度流需要在用户授权后才能验证
      return {
        hasDepth: false,
        method: 'h5-depth-declared',
        detail: 'H5 声明支持 depth 但实际可用性极低，按无景深处理',
      }
    } catch (_) {
      return { hasDepth: false, method: 'h5-depth-check-fail', detail: 'H5 depth 约束验证失败' }
    }
  } catch (e) {
    console.warn('[depthDetect] H5 景深检测异常:', e)
    return { hasDepth: false, method: 'h5-error', detail: `H5 检测异常: ${e.message}` }
  }
}
