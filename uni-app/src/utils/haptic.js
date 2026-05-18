/**
 * 达标震动：H5 用 navigator.vibrate；App 用 uni.vibrateShort；失败静默。
 */
export function hapticReady() {
  if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
    try {
      navigator.vibrate(40)
    } catch (_) {
      /* ignore */
    }
    return
  }

  try {
    const ret = uni.vibrateShort({
      type: 'medium',
      fail: () => {},
    })
    if (ret && typeof ret.catch === 'function') {
      ret.catch(() => {})
    }
  } catch (_) {
    /* ignore */
  }
}
